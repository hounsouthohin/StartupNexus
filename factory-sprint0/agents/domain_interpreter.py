"""
agents/domain_interpreter.py
─────────────────────────────
Nœud LLM focalisé sur l'interprétation du DOMAINE MÉTIER.

Responsabilité unique : extraire les modèles Prisma et les enums d'un brief libre.
NE touche pas aux pages, aux routes ni aux labels — c'est le rôle de page_planner.

Découplage délibéré :
- Les règles de déduction modèle (userId, enums, relations) sont ici → les modifier
  sans risquer de perturber le calcul des routes.
- Les règles de routing (page patterns, segments [id]/[slug]) sont dans page_planner.py.

Pipeline :
    brief_writer (libre) → domain_interpreter → page_planner → semantic_annotator → ...
    brief structuré (models présents) → [skip domain_interpreter] → page_planner si pas de pages
"""
from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Prompt — règles domaine uniquement
# ─────────────────────────────────────────────────────────────────────────────

_DOMAIN_STACK_INVARIANTS = """\
## RÈGLES STACK — MODÈLES (NON NÉGOCIABLES)

### Auth
- Auth = Clerk V6 uniquement. JAMAIS : bcrypt, jwt, password, next-auth.
- **JAMAIS de modèle `User` dans le schema Prisma.** Clerk gère les utilisateurs. `userId` est une String externe.
- **Défaut : tout modèle possède un owner** → `userId String` (y compris les lookups : Category, Tag,
  Type, Label...). La factory est single-tenant : chaque utilisateur possède SES propres données.
  Exception `authorId String` à la place de `userId` pour le modèle principal d'un CMS/blog.
- Les sous-modèles enfants (ex: Comment d'une Task) utilisent le FK du parent ET ont aussi `userId String` en propre.
- **EXCEPTION — catalogue GLOBAL (sans owner)** : si le brief décrit une entité **partagée entre tous
  les utilisateurs**, existant indépendamment de qui la crée (ex: les *espaces* réservables d'un
  coworking, les *salles* d'un planning, un *catalogue de produits* commun), alors ce modèle
  N'A PAS de `userId`. Signaux : « les X que tout le monde peut réserver/consulter », « le catalogue »,
  « les ressources partagées ». Dans le doute, garde `userId` (défaut). N'applique JAMAIS cette
  exception à des données personnelles (mes tâches, mes demandes, mes notes).
- **RÔLES ≠ modèle**. Si le brief distingue plusieurs ACTEURS (employé vs admin, membre vs gestionnaire),
  ne crée PAS de modèle `Role`/`Admin` et n'ajoute PAS de champ `role` : Clerk porte le rôle
  (publicMetadata). Le multi-acteur est déclaré ailleurs (Semantic Annotator), pas dans les modèles.
  N'aplatis pas non plus les deux acteurs en un seul : garde le brief tel quel, les rôles sont traités en aval.

### Champs obligatoires dans tout modèle
- `id String @id @default(uuid())`
- `createdAt DateTime @default(now())`
- `updatedAt DateTime @updatedAt`

### Relations — déclaration stricte
- Le modèle ENFANT déclare : `taskId String` + `task Task @relation(fields: [taskId], references: [id], onDelete: Cascade)`
- Le modèle PARENT déclare juste : `comments Comment[]`
- Ne jamais déclarer @relation sur les deux côtés

### Format des modèles (CRITIQUE)
Chaque modèle est une STRING sur une seule ligne :
`"ModelName { field1 Type1 attrs1, field2 Type2 attrs2, ... }"`
Les virgules DANS les attributs @relation(..., ...) ne comptent PAS comme séparateurs.

### Enums
`{ "NomEnum": ["valeur1", "valeur2"] }` — valeurs en snake_case minuscules\
"""

_DOMAIN_DEDUCTION_RULES = """\
## RÈGLES DE DÉDUCTION MODÈLE

### RÈGLE 1 — Préservation des champs
Si le brief décrit un attribut comme une valeur simple, **conserver ce champ tel quel dans le modèle**.
- `category String` dans le brief → champ `category String` dans Prisma. **NE PAS créer un modèle `Category`.**
- **Créer un modèle séparé UNIQUEMENT si le brief dit EXPLICITEMENT** que l'entité est créée, listée ou gérée séparément.

### RÈGLE 2 — enum vs Boolean
Si exactement 2 valeurs dont l'une est `published`, `active`, `enabled`, `visible` — c'est un `Boolean @default(false)`. PAS un enum.
Phrasés qui déclenchent **enum** : 3 états ou plus, ou workflow de transition nommé.

### RÈGLE 3 — Modèle lookup et FK obligatoire
Si tu crées un modèle séparé (Category, Tag...), le modèle principal DOIT référencer ce lookup via une FK.
Recipe avec Category → Recipe DOIT avoir `categoryId String` + `category Category @relation(...)`.

### RÈGLE 4 — Valeurs finies → enum Prisma (jamais String @default)
Tout champ dont les valeurs sont finies DOIT être déclaré comme enum Prisma.
**ERREUR** : `status String @default("active")`
**CORRECT** : `status ProjectStatus @default(active)` + `"ProjectStatus": ["active", "paused"]` dans enums.

### RÈGLE 5 — Many-to-many (PLUSIEURS valeurs d'un lookup géré séparément)
Si le brief dit qu'une entité peut avoir **PLUSIEURS** valeurs d'un lookup géré séparément
(ex: "un article a plusieurs tags", "un produit appartient à plusieurs collections") :
- Les DEUX modèles déclarent un champ tableau, SANS FK et SANS @relation :
  `Post { ..., tags Tag[] }` et `Tag { ..., posts Post[] }`
- **JAMAIS de champ `tagId String`** (ce serait une valeur unique) ni de modèle pivot manuel (PostTag).
- Ne pas confondre avec le 1-N : "un commentaire appartient à UN post" → FK `postId` + @relation (RÈGLE classique).
Signaux M2M : "plusieurs X", "des tags", "multi-catégories", "peut appartenir à plusieurs".\
"""

_DOMAIN_FEW_SHOT = """\
## EXEMPLES — ILLUSTRATION DU FORMAT UNIQUEMENT
⚠ Ces exemples montrent la FORME attendue (syntaxe Prisma, structure JSON), PAS des gabarits de domaine.
Déduis TOUJOURS les modèles, champs et enums du brief réel. Si le brief parle de bibliothèque, de cabinet
médical ou de covoiturage, n'y plaque JAMAIS les entités ci-dessous (Task, Post, Client…).

## EXEMPLES — MODÈLES UNIQUEMENT

### Brief : "Gestion de tâches avec commentaires. Statut : pending/in_progress/done."
```json
{
  "models": [
    "Task { id String @id @default(uuid()), title String, description String?, status TaskStatus @default(pending), userId String, createdAt DateTime @default(now()), updatedAt DateTime @updatedAt, comments Comment[] }",
    "Comment { id String @id @default(uuid()), content String, taskId String, task Task @relation(fields: [taskId], references: [id], onDelete: Cascade), userId String, createdAt DateTime @default(now()), updatedAt DateTime @updatedAt }"
  ],
  "enums": {
    "TaskStatus": ["pending", "in_progress", "done"]
  }
}
```

### Brief : "Blog personnel. Statut : brouillon ou publié. Catégorie est un champ simple."
```json
{
  "models": [
    "Post { id String @id @default(uuid()), title String, excerpt String?, published Boolean @default(false), category String, authorId String, slug String @unique, createdAt DateTime @default(now()), updatedAt DateTime @updatedAt }"
  ],
  "enums": {}
}
```

### Brief : "Blog avec articles et tags. Un article peut avoir plusieurs tags, les tags sont gérés dans une liste dédiée."
```json
{
  "models": [
    "Post { id String @id @default(uuid()), title String, content String, published Boolean @default(false), slug String @unique, tags Tag[], authorId String, createdAt DateTime @default(now()), updatedAt DateTime @updatedAt }",
    "Tag { id String @id @default(uuid()), name String, posts Post[], userId String, createdAt DateTime @default(now()), updatedAt DateTime @updatedAt }"
  ],
  "enums": {}
}
```
(M2M — RÈGLE 5 : tableau des deux côtés, aucun tagId, aucun @relation, aucun modèle pivot.)

### Brief : "App de facturation. Clients + factures (draft/sent/paid). Clients gérés dans liste dédiée."
```json
{
  "models": [
    "Client { id String @id @default(uuid()), name String, email String, userId String, invoices Invoice[], createdAt DateTime @default(now()), updatedAt DateTime @updatedAt }",
    "Invoice { id String @id @default(uuid()), amount Float, status InvoiceStatus @default(draft), clientId String, client Client @relation(fields: [clientId], references: [id], onDelete: Cascade), userId String, createdAt DateTime @default(now()), updatedAt DateTime @updatedAt }"
  ],
  "enums": {
    "InvoiceStatus": ["draft", "sent", "paid"]
  }
}
```\
"""

_DOMAIN_FORMAT = """\
## FORMAT DE SORTIE — JSON uniquement

```json
{
  "models": ["ModelName { field Type attrs, ... }", ...],
  "enums": { "EnumName": ["val1", "val2"] }
}
```

Retourne UNIQUEMENT le JSON. Aucune explication, aucun markdown.\
"""

_DOMAIN_SYSTEM_PROMPT = "\n\n".join([
    (
        "Tu es un architecte de domaine expert de la stack Prisma 7 + PostgreSQL.\n"
        "Ta mission UNIQUE : extraire les modèles Prisma et les enums d'un brief applicatif.\n"
        "Ne génère PAS de pages, routes, labels ni design_system — c'est une autre étape."
    ),
    _DOMAIN_STACK_INVARIANTS,
    _DOMAIN_DEDUCTION_RULES,
    _DOMAIN_FEW_SHOT,
    _DOMAIN_FORMAT,
])


# ─────────────────────────────────────────────────────────────────────────────
# Node
# ─────────────────────────────────────────────────────────────────────────────

async def domain_interpreter_node(state: dict) -> dict:
    """
    Interprète le domaine métier d'un brief libre : extrait models + enums.

    Skip si brief contient déjà des models.
    Fail-safe : toute erreur LLM lève ApplicationError (non retryable — brief invalide).
    """
    from temporalio.exceptions import ApplicationError

    brief = state.get("brief", {})

    if brief.get("models"):
        logger.info("[domain_interpreter] models déjà présents → skip")
        return {}

    description = brief.get("description", "").strip()
    hints = brief.get("hints", {}) or {}

    if not description:
        raise ApplicationError(
            "domain_interpreter: description vide — impossible d'extraire le domaine.",
            non_retryable=True,
        )

    from agents.llm_provider import get_chat_llm
    from langchain_core.messages import SystemMessage, HumanMessage as _HM
    from agents.stack_config import get_llm_models as _get_llm_models

    _arch_model = _get_llm_models().get("architect_base", "gpt-4o-mini")
    llm = get_chat_llm(
        model=_arch_model,
        temperature=0.0,
        api_key=os.getenv("ARCHITECT_API_KEY", os.getenv("OPENAI_API_KEY")),
    ).bind(response_format={"type": "json_object"})

    hint_str = (
        f"\n\nHints du développeur :\n{json.dumps(hints, ensure_ascii=False)}"
        if hints else ""
    )
    user_msg = f"Brief : {description}{hint_str}"

    try:
        response = await llm.ainvoke([
            SystemMessage(content=_DOMAIN_SYSTEM_PROMPT),
            _HM(content=user_msg),
        ])
        result: dict = json.loads(response.content)
    except json.JSONDecodeError as e:
        raise ApplicationError(f"domain_interpreter: réponse non-JSON — {e}", non_retryable=False)
    except Exception as e:
        raise ApplicationError(f"domain_interpreter: erreur LLM — {e}", non_retryable=False)

    if not result.get("models"):
        raise ApplicationError(
            "domain_interpreter: aucun modèle généré — brief trop vague ?",
            non_retryable=False,
        )

    model_names = [m.split()[0] for m in result.get("models", []) if m.split()]
    logger.info("[domain_interpreter] ✓ %d modèle(s) : %s", len(model_names), model_names)

    updated_brief = {
        **brief,
        "models": result.get("models", []),
        "enums": result.get("enums", {}),
    }
    return {"brief": updated_brief}
