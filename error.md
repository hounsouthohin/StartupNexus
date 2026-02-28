2) Pourquoi certains champs JSON ne sont pas encore utilisés
Raison principale: migration incomplète vers “config-driven”.

Le champ existe dans la config, mais aucun code n’en lit la valeur.
Typiquement:
qdrant_filter: présent, mais retrieval architect continue avec sa logique actuelle.
commands: présents, mais run_build/run_tests utilisent encore des commandes codées.
test_import_rules, spec_validation: déclaratifs, mais pas encore branchés dans les fonctions qui valident/réécrivent. Y A T IL UNE RAISON A CELA est ce fait expret pour les sprint avenir?


Exemple concret avec ta stack actuelle.

Ta config peut être **100% valide au schéma** (donc “passe”), mais le run échoue quand même:

1. `qdrant_filter` existe et est bien formé dans le JSON  
- Schéma: OK  
- Réalité: si le code retrieval ne lit pas `qdrant_filter`, aucun filtrage stack n’est appliqué.

2. `commands.test = "npx jest --coverage"` est correct  
- Schéma: OK  
- Réalité: si le code exécute une commande hardcodée différente, ton champ n’a aucun effet.

3. `spec_validation.required_sections` est correct  
- Schéma: OK  
- Réalité: si `architect.py` continue d’utiliser une liste hardcodée, ta config n’est pas utilisée.

4. `dev_packages` est bien défini  
- Schéma: OK  
- Réalité: si `dev.py` ne pousse pas ces devDependencies dans la génération, le `package.json` final peut être incomplet -> tests/build échouent.

Donc:
- Le schéma vérifie “le JSON est bien écrit”.
- Seul un run d’acceptance vérifie “le système se comporte comme attendu avec ce JSON”.

1. **Faiblesse de la concaténation des prompts (scaling prompt)**
- Aujourd’hui on fait: `base_prompt + rules_stack`.
- Tant que les règles sont courtes, ça marche.
- Quand les règles grossissent:
  - conflits/incohérences entre règles,
  - dilution des priorités (le modèle ne sait plus quoi appliquer en premier),
  - surcharge de contexte (moins de place pour la tâche réelle).
- Symptôme: outputs moins stables, oubli de contraintes critiques, plus d’hallucinations “conformes en surface”.
- Nom court: **Prompt Concat Scalability Risk**.

2. **Décalage config-exécution (Config-Runtime Drift)**
- La config déclare des champs (`qdrant_filter`, `commands`, `spec_validation`, etc.), mais le runtime ne les consomme pas toujours.
- Donc:
  - la config “passe” au schéma,
  - mais n’influence pas réellement le comportement.
- Symptôme: sentiment de contrôle via config, alors que la logique reste hardcodée ailleurs.
- Impact: stack-as-config partiel, onboarding nouvelle stack trompeur.
- Nom court: **Config-Runtime Drift**.

