### quelles techniques ou quelle ressources de connaissance peut on ajouter : à ceux ci : standards + standards


### IL faudra verifier encore une fois apres l'application du plan.md, l'aspect générique des guards



#### Recommandation concrète (conforme plan)

~~Ajouter une étape brief_normalizer_activity avant architect_activity.~~
~~Sortie normalizer: JSON canonique (models, fields, pages, api_routes, auth, security, tests).~~
~~Faire valider ce JSON par schéma + (optionnel) humain.~~
~~Donner à Architect ce JSON en entrée (au lieu de seule phrase).~~

> ABSORBÉ — Brief normalizer implémenté dans Phase A de la Refactorisation Architecture Simplifiée (27-28 Mars 2026). Le pipeline Architect a été réécrit avec brief_normalizer → retrieval → planner → spec_writer → formatter.




NOUVELLES IDÉES (identifiées pendant l'audit)
I1 — agent_context multi-niveaux dans Qdrant
Introduire agent_context=architect pour les zones 15/16 (conformité/sécurité). L'Architect recevrait des standards de "design correct" (comment structurer les relations Prisma, patterns sécurité applicative), le Dev garderait agent_context=dev pour les standards d'implémentation. Séparation claire des responsabilités dans le RAG.

~~I2 — commons issu du blueprint JSON~~
~~Les 6 fichiers hardcodés dans dev.py (commons = {"next.config.js", "app/layout.tsx", ...}) pourraient venir du champ blueprint.required_files du JSON.~~

> ABSORBÉ — templates et required_files maintenant lus depuis le JSON stack (Stack-as-Config Sprint 3 + cleanup Phase B refactorisation).

I3 — Temperature par node dans le JSON
Exposer {"brief_normalizer_temperature": 0.0, "planner_temperature": 0.0, "spec_writer_temperature": 0.1} dans le JSON stack. Permet d'ajuster par stack sans toucher au Python.

I4 — Unified anti-drift rules source
Extraire les règles anti-drift (présentes dans 3 nodes) dans rules_architect.md comme source unique. Les nodes Brief Normalizer et Planner lisent et injectent ce fichier. Fin de la dérive de cohérence.


###### ENVISAGER un agent pour la gestion des templates