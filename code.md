Le système actuel de traitement des erreurs
Ce qui se passe aujourd'hui

tsc --noEmit
    ↓
_parse_tsc_errors_for_files()     ← filtre : erreurs dans fichiers écrits CE tour seulement
    ↓
boucle for err_line in errors:
    ├── A2 : lire lignes fichier autour de l'erreur    (pour TS2304/TS2724)
    └── E1 : message "crée le fichier"                 (pour TS2307 local)
    ↓
errors_enriched → HumanMessage → LLM corrige
tsc voit tout — il retourne tous les codes d'erreur TypeScript existants. Mais ce qu'on envoie au LLM c'est un texte brut du genre :


app/page.tsx(2,26): error TS2307: Cannot find module '@/components/TaskList'
Pourquoi on est obligé de raffiner
Le LLM reçoit ce texte et doit :

Comprendre ce que l'erreur signifie
Comprendre quelle action concrète elle implique
Agir sur le bon fichier
Le problème : les messages tsc sont conçus pour des développeurs humains qui ont le contexte complet dans leur tête. Le LLM, lui, a deux faiblesses structurelles :

Faiblesse 1 — Dérive de mémoire : le LLM a écrit app/page.tsx à l'itération N. À l'itération N+2, quand il reçoit une erreur sur ce fichier, il ne "voit" plus le fichier — il l'imagine depuis sa mémoire d'entraînement. Sans A2 (injection du vrai contenu), il réécrit le fichier comme il croit qu'il devrait être → réintroduit le blog anchor ou invente d'autres types.

Faiblesse 2 — Ambiguïté d'action : TS2307 Cannot find module peut vouloir dire deux choses complètement opposées :

Dépendance npm manquante → npm install X
Fichier local non créé → write_file('components/X.tsx', ...)
Sans indication, le LLM choisit au hasard (ou choisit l'option la plus "évidente" de son entraînement, souvent la mauvaise dans ce contexte).

Risques du système actuel
Risque 1 — Explosion combinatoire

TypeScript a ~300 codes d'erreur. On en traite 3. Chaque nouveau run peut révéler une nouvelle classe :


TS2322  type incompatible         → LLM ne sait pas quel type corriger
TS2339  propriété inexistante     → LLM réécrit tout le modèle
TS2345  argument de type faux     → LLM invente une conversion
TS2531  object possibly null      → LLM ajoute des ! partout
TS2366  not all paths return      → LLM ajoute des return undefined
...
À chaque run raté on ajoute un if dans file_validate_node. Dans 6 mois, la fonction fait 300 lignes de conditions imbriquées.

Risque 2 — Couplage dur dans le code

Aujourd'hui la logique de traitement d'erreurs est dans le graphe LangGraph (file_validate_node). Chaque ajout :

Nécessite un redéploiement Docker
Mélange la logique de routage du graphe avec la logique métier d'erreur
Rend les tests difficiles (tester A2 implique de mocker tout le graphe)
Risque 3 — Zéro feedback loop

On ne sait pas si E1 ou A2 ont réellement aidé le LLM à corriger. Est-ce que le LLM a suivi l'instruction "crée le fichier" ? Ou a-t-il ignoré le message et modifié l'import quand même ? On détecte ça seulement au run suivant, pas en temps réel.

Risque 4 — Pas de priorité ni d'ordre

Si un fichier a 4 erreurs différentes (TS2307 + TS2322 + TS2339 + TS2304), toutes reçoivent le même traitement. Pourtant la correction de TS2307 (créer le fichier manquant) peut faire disparaître les 3 autres. Aujourd'hui le LLM reçoit 4 messages enrichis sans savoir lequel traiter en premier.

Solutions possibles
Solution 1 — Error Rule Engine (court terme, ~1 sprint)

Transformer les if hardcodés en une structure de données déclarative :


# agents/tsc_error_rules.py
TSC_ERROR_RULES = [
    {
        "code": "TS2307",
        "condition": lambda mod, _: mod.startswith("@/") or mod.startswith("./"),
        "extract": lambda m: m.group(1),   # le chemin du module
        "priority": 1,                      # traiter en premier
        "message": lambda mod: (
            f"FICHIER MANQUANT : '{mod}' n'existe pas.\n"
            f"Crée '{_to_file_path(mod)}' avec write_file — ne modifie pas l'import."
        ),
    },
    {
        "code": "TS2304",
        "condition": lambda name, _: True,
        "extract": lambda m: m.group(1),
        "priority": 2,
        "message": lambda name: (
            f"Nom '{name}' introuvable. Vérifie lib/types.ts — utilise uniquement les noms exportés."
        ),
    },
    # Ajouter une nouvelle erreur = ajouter un dict ici, zéro logique modifiée
]
file_validate_node devient un simple moteur qui itère sur ces règles. Ajouter une nouvelle classe d'erreur = ajouter un dict, pas toucher au graphe.

Solution 2 — Standards Qdrant pour les erreurs (moyen terme, Sprint 5)

Stocker les patterns d'erreur dans Qdrant (ZONE dédiée, ex: ZONE_18 "error patterns") :


ACTION: OBLIGATOIRE
CODE: TS2307
CONDITION: module commence par @/ ou ./
DIAGNOSTIC: fichier local manquant — ne pas modifier l'import
FIX: write_file('<chemin converti>', ...)
ERREUR_ATTENDUE: Cannot find module '@/...'
Quand file_validate_node détecte une erreur, il fait un RAG search sur le code d'erreur et injecte le standard dans le message. Ajouter une nouvelle classe d'erreur = ajouter un standard Qdrant via approve_suggestion.py, zéro code Python.

C'est l'alignement naturel avec la vision du Learner : le Learner détecte un pattern d'erreur récurrent → génère un standard ZONE_18 → validé humainement → le prochain run en bénéficie automatiquement.

Solution 3 — Superviseur Compilabilité (long terme, Sprint 4.6)

C'est déjà dans la roadmap (#34). Un agent dédié qui reçoit toutes les erreurs build + contexte complet et génère des instructions chirurgicales. Plus de traitement d'erreur dans file_validate_node — tout est délégué. C'est la solution propre mais elle nécessite l'infrastructure Sprint 4.6.

Recommandation
Horizon	Solution	Effort	Impact
Maintenant	E1 fait, accepter les limites	Fait	Corrige le run actuel
Sprint actuel	Error Rule Engine (Solution 1)	~2h	Élimine l'explosion du code
Sprint 5	Standards Qdrant ZONE_18	~1 sprint	Zéro code pour les nouvelles erreurs
Sprint 4.6	Superviseur Compilabilité	1 sprint complet	Solution propre finale
La Solution 1 est le bon investissement maintenant : elle ne change pas l'architecture, elle structure ce qu'on a déjà avant que ça explose.