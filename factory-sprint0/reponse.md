**Audit complet (état actuel de ton workspace)**

1. **Critique - Le socle de validation Sprint est cassé par cohérence**
- Ton seul test actif dépend de fichiers supprimés: `docs/SUPERVISEUR_DRAFT_v0.md`, `logs/shadow/learner_shadow_log.json`, etc.
- Preuve: [test_sprint1_validation.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\tests\test_sprint1_validation.py:34), [test_sprint1_validation.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\tests\test_sprint1_validation.py:247).
- Impact: état non validable tant que la suite n’est pas réalignée avec Sprint 2.

2. **Critique - Script de nettoyage potentiellement destructeur sur les assets suivis Git**
- `cleanup_generated.py` supprime explicitement `app/`, `src/`, `tests/*`, `package.json`, `tsconfig.json`, `middleware.ts`, logs.
- Preuve: [cleanup_generated.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\scripts\cleanup_generated.py:15), [cleanup_generated.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\scripts\cleanup_generated.py:27), [cleanup_generated.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\scripts\cleanup_generated.py:45).
- Impact: il peut rendre le repo “non-runnable” en un run, ce qui correspond exactement à l’état observé.

3. **Majeur - Risque de suppression hors workspace généré**
- En fin de `dev_agent`, le cleanup utilise `cleanup_dir` relatif (`"."` ou sous-dossier) sans le rebaser explicitement sur `FACTORY_WORKDIR`.
- Preuve: [dev.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\agents\dev.py:471), [dev.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\agents\dev.py:472).
- Impact: selon le cwd du worker, suppression possible au mauvais endroit (`node_modules`, `.next`, `__pycache__`).

4. **Majeur - Incohérences fonctionnelles Stack/Prompts/Docs**
- Config interdit `shadcn/ui` mais QA prompt et README en parlent encore.
- Preuves: [nextjs-clerk-prisma.json](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\config\stacks\nextjs-clerk-prisma.json:94), [prompts/qa.md](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\prompts\qa.md:19), [README](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\README:9).
- Impact: génération contradictoire, plus de variabilité et erreurs non déterministes.

5. **Majeur - Contrat Architect encore trop permissif**
- `specification` reste validée à `minLength: 500` sans exigences sémantiques fortes.
- Preuve: [architect_agent_contract.json](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\schemas\contracts\architect_agent_contract.json:45).
- Impact: une spec longue mais faible peut passer le gate.

6. **Majeur - RAG Architect non enrichi (requête brute)**
- Le retrieval utilise directement la phrase utilisateur, sans query expansion technique.
- Preuve: [architect.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\agents\architect.py:246), [architect.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\agents\architect.py:248).
- Impact: qualité RAG instable sur demandes métier abstraites.

7. **Majeur - Graph Architect toujours linéaire (pas de vrai nœud critique)**
- Chaîne stricte `retrieval -> planner -> spec_writer -> diagrammer -> formatter`.
- Preuve: [architect.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\agents\architect.py:429).
- Impact: pas de boucle explicite “évaluer/corriger” globale avant sortie.

8. **Moyen - `shared_tools.py` redevient un module monolithique**
- Taille ~34 KB et forte concentration des responsabilités.
- Preuve: [shared_tools.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\agents\shared_tools.py), statut taille relevé.
- Impact: dette de maintenance, faible lisibilité, couplage élevé.

9. **Moyen - Défaut Python classique: argument mutable par défaut**
- `run_tests(project_dir=".", files={})`.
- Preuve: [shared_tools.py](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\agents\shared_tools.py:596).
- Impact: comportement inattendu possible entre appels.

10. **Moyen - Dépendances Python fragiles**
- `requirements.txt` mélange `langchain-openai` et `langchain_openai`, beaucoup de versions non pinées.
- Preuve: [requirements.txt](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\requirements.txt:6), [requirements.txt](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\requirements.txt:12).
- Impact: reproductibilité faible selon l’environnement.

11. **Moyen - Mismatch documentaire et historique**
- `project_analysis.md` et plusieurs docs ne reflètent plus l’état actuel.
- Preuve: [project_analysis.md](C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0\project_analysis.md:32).
- Impact: diagnostic trompeur pour les prochains sprints.

12. **Moyen - Traçabilité Git faible**
- Historique récent majoritairement `changes`.
- Impact: difficile de relier régression -> commit précis.

**Point d’évolution positif**
- `shared_tools.py` est revenu (non-tracké) donc la rupture d’imports globale vue précédemment n’est plus la faille principale immédiate.

**Ce que je n’ai pas exécuté**
- Je n’ai pas relancé une suite `pytest` complète ici, car l’audit statique montre déjà des préconditions manquantes dans les tests Sprint.

**Plan de remise en état minimal**
1. Aligner `tests/test_sprint1_validation.py` sur Sprint 2 (ou restaurer les artefacts attendus).
2. Sécuriser `cleanup_generated.py` (dry-run par défaut + garde “repo clean” + périmètre explicite).
3. Corriger `dev.py` cleanup pour qu’il opère strictement sous `FACTORY_WORKDIR`.
4. Harmoniser stack config, prompts et docs (notamment `shadcn/ui`).
5. Durcir le contrat Architect + ajouter un nœud critique explicite dans le graph.