"""
scripts/validate_contracts.py
Validation runtime des contrats JSON Schema — Software Agent Factory

Usage autonome (pour debug / CI) :
    python scripts/validate_contracts.py

Usage dans les activities Temporal :
    from scripts.validate_contracts import validate_input, validate_output
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print("❌ Module 'jsonschema' manquant. Exécute : pip install jsonschema")
    sys.exit(1)

# ─────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = BASE_DIR / "schemas" / "contracts"

AGENT_CONTRACT_FILES = {
    "architect_agent": "architect_agent_contract.json",
    "dev_agent":       "dev_agent_contract.json",
    "test_agent":      "test_agent_contract.json",
    "qa_agent":        "qa_agent_contract.json",
    "github_agent":    "github_agent_contract.json",
    "dev_test_agent": "dev_test_agent_contract.json",
    "learner_agent":  "learner_agent_contract.json",
}

# ─────────────────────────────────────────────────────
# Chargement des contrats
# ─────────────────────────────────────────────────────

def load_contract(agent_id: str) -> Dict:
    if agent_id not in AGENT_CONTRACT_FILES:
        raise ValueError(
            f"Agent inconnu : {agent_id!r}\n"
            f"Agents supportés : {', '.join(AGENT_CONTRACT_FILES)}"
        )

    contract_path = CONTRACTS_DIR / AGENT_CONTRACT_FILES[agent_id]

    if not contract_path.is_file():
        raise FileNotFoundError(
            f"Contrat introuvable : {contract_path}\n"
            f"→ Vérifiez que le fichier existe dans schemas/contracts/"
        )

    with contract_path.open(encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────
# Validation core
# ─────────────────────────────────────────────────────

def validate_input(
    agent_id: str,
    input_data: Any,
    raise_on_error: bool = True
) -> bool:
    contract = load_contract(agent_id)
    schema = contract.get("input_schema") or {}

    if not schema:
        print(f"⚠️  [{agent_id}] Pas de input_schema défini → validation ignorée")
        return True

    try:
        validate(instance=input_data, schema=schema)
        print(f"✅ [{agent_id}] Input valide")
        return True
    except ValidationError as e:
        path = " → ".join(str(p) for p in e.absolute_path) or "(racine)"
        msg = (
            f"❌ [{agent_id}] Input invalide\n"
            f"   Champ : {path}\n"
            f"   Message : {e.message}\n"
            f"   Valeur reçue : {repr(e.instance)[:180]}"
        )
        print(msg)
        if raise_on_error:
            raise ValidationError(msg) from e
        return False


def validate_output(
    agent_id: str,
    output_data: Any,
    raise_on_error: bool = True
) -> bool:
    contract = load_contract(agent_id)
    schema = contract.get("output_schema") or {}

    if not schema:
        print(f"⚠️  [{agent_id}] Pas de output_schema défini → validation ignorée")
        return True

    try:
        validate(instance=output_data, schema=schema)
        print(f"✅ [{agent_id}] Output valide")
        return True
    except ValidationError as e:
        path = " → ".join(str(p) for p in e.absolute_path) or "(racine)"
        msg = (
            f"❌ [{agent_id}] Output invalide\n"
            f"   Champ : {path}\n"
            f"   Message : {e.message}\n"
            f"   Valeur reçue : {repr(e.instance)[:180]}"
        )
        print(msg)
        if raise_on_error:
            raise ValidationError(msg) from e
        return False


# ─────────────────────────────────────────────────────
# Mode autonome — tests mock corrigés
# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "═"*70)
    print(" 🔐 VALIDATION CONTRATS — Software Agent Factory  (Sprint 1 — B2)")
    print("═"*70 + "\n")

    # Vérification existence & structure minimale
    print("Vérification intégrité contrats...")
    all_ok = True
    for agent in AGENT_CONTRACT_FILES:
        try:
            contract = load_contract(agent)
            has_input  = bool(contract.get("input_schema"))
            has_output = bool(contract.get("output_schema"))
            status = "✅ OK" if has_input and has_output else "⚠️ incomplet"
            print(f"  {agent:16} → {status}")
            if not (has_input and has_output):
                all_ok = False
        except Exception as e:
            print(f"  {agent:16} → ❌ {e}")
            all_ok = False

    print()

    # Tests mock corrigés (assez longs pour passer minLength)
    print("Tests mock de validation...\n")

    # ── Input valide ────────────────────────────────────────────────
    validate_input("architect_agent", {
        "phrase": "Crée un SaaS de gestion de tâches avec authentification Clerk et notifications en temps réel",
        "project_name": "taskflow-pro"
    })

    # ── Input invalide (phrase trop courte) ─────────────────────────
    validate_input("architect_agent", {
        "phrase": "ok",
        "project_name": "test"
    }, raise_on_error=False)

    # ── Output architect valide (assez long pour minLength 500 + 100) ──
    validate_output("architect_agent", {
        "specification": (
            "# Spécification Technique Complète – Projet TaskFlow Pro\n\n"
            "## Objectif du produit\n"
            "Développer un SaaS moderne de gestion de tâches collaboratif, "
            "avec une authentification sécurisée via Clerk, un CRUD complet, "
            "des notifications en temps réel et un dashboard analytics.\n\n"
            "## Fonctionnalités principales\n"
            "- Authentification multi-méthodes (email, Google, GitHub) via Clerk\n"
            "- Création, modification, suppression et archivage de tâches\n"
            "- Priorités (haute/moyenne/basse), deadlines, étiquettes\n"
            "- Commentaires et pièces jointes sur les tâches\n"
            "- Notifications push / email / in-app en temps réel\n"
            "- Tableau Kanban + liste + calendrier\n"
            "- Recherche full-text et filtres avancés\n"
            "- Mode sombre / clair + responsive mobile-first\n\n"
            "## Stack technique imposée\n"
            "- Frontend : Next.js 14 App Router + Server Components\n"
            "- Auth : Clerk v5+\n"
            "- Backend/DB : Prisma + PostgreSQL\n"
            "- UI : shadcn/ui + Tailwind CSS\n"
            "- Validation : Zod (client + serveur)\n"
            "- Tests : Jest (unit) + Playwright (E2E)\n"
            "- Déploiement : Vercel avec CI/CD GitHub Actions\n\n"
            "## Sécurité & bonnes pratiques\n"
            "- Validation Zod sur tous les inputs\n"
            "- Rate limiting API publiques\n"
            "- Protection CSRF via Clerk middleware\n"
            "- Pas d’exposition de secrets côté client\n"
            "- OWASP Top 10 couvert\n\n"
            "Cette spécification couvre un MVP production-ready avec scalabilité future."
        ),
        "mermaid_diagram": (
            "graph TD\n"
            "    User[Utilisateur] -->|Authentification| Clerk[Clerk Auth]\n"
            "    Clerk --> App[Application Next.js]\n"
            "    App --> API[API Routes]\n"
            "    API --> Prisma[Prisma ORM]\n"
            "    Prisma --> PostgreSQL[Base PostgreSQL]\n"
            "    App --> Realtime[WebSocket / Pusher]\n"
            "    Realtime --> Notifications[Notifications temps réel]\n"
            "    User -->|CRUD Tâches| App\n"
            "    App -->|Analytics| Dashboard[Tableau de bord]\n"
            "    style User fill:#f9f,stroke:#333\n"
            "    style Clerk fill:#a8d,stroke:#333\n"
            "    style PostgreSQL fill:#ff9,stroke:#333"
        )
    })

    # ── Output qa_agent valide (exemple dict) ───────────────────────
    validate_output("qa_agent", {
        "e2e_tests": {
            "tests/e2e/login.spec.ts": "// test login avec Clerk\nawait page.goto('/sign-in'); ...",
            "tests/e2e/task-creation.spec.ts": "// création tâche\nawait page.fill('input[name=title]', 'Test tâche'); ..."
        }
    })

    # ── Output github_agent valide ──────────────────────────────────
    validate_output("github_agent", {
        "pr_url":   "https://github.com/org/taskflow-pro/pull/42",
        "repo_url": "https://github.com/org/taskflow-pro"
    })

    print("\n" + "═"*70)
    print("Statut final : " + ("TOUT EST OK ✅" if all_ok else "PROBLÈMES DÉTECTÉS ⚠️"))
    print("═"*70 + "\n")
