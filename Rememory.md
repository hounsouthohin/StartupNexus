Sprint 4 — Liste complète des accords
Groupe 1 — Déjà dans ma liste mais incomplet
#	Item	Ce que j'avais dit	Ce que j'avais omis
1	Architect prompt fix	prompt_rules dans JSON	Le champ requirements doit être ajouté à l'output contract de l'Architect aussi
2	Blueprint Validator BLOQUANT	WARNING → BLOQUANT	DevAgent doit itérer jusqu'à complétion avant run_build (pas juste erreur)
3	QA agent fix	passer combined_files	Les tests générés doivent vérifier les routes et pages réellement présentes
4	Run de validation	—	—
Groupe 2 — Complètement oublié par moi
#	Item	Source
5	spec_coverage script	Discuté explicitement — script Python, pas agent
6	Contracts inter-agents v2	Roadmap + discussion : router_type, stack_id, required_files dans l'output Architect
7	Anti-patterns automatiques	LearnerAgent crée des anti-patterns Qdrant depuis les run failures
8	Gate Décisionnel	>15 suggestions learner, >70% validation humaine → signal clôture Sprint 4
9	Qdrant Governance v1	`status: active
10	approve_suggestion.py	Script 30 lignes, validation humaine learner suggestions → upsert Qdrant
11	SLA approve_suggestion	Engagement de review dans un délai défini (sinon boucle d'apprentissage bloquée)
Groupe 3 — Residuels audit Sprint 3 (non bloquants mais notés)
#	Item
12	env_validation regex branché dans le runtime
13	test_sprint1_validation.py archivé comme legacy
14	validate_config_consumption.py : validation par composant (pas juste regex globale)
Sprint 4.5 — Couche Valeur Client (à discuter maintenant)
La remarque de l'autre IA était juste : la factory génère du code qui compile, mais pas forcément une app qui apporte de la valeur à un utilisateur.

Sprint 4 = "est-ce que ça build ?"
Sprint 4.5 = "est-ce que l'utilisateur peut réellement s'en servir ?"

Ma proposition concrète pour Sprint 4.5 :

Objectif : après spec_coverage, vérifier que les flux utilisateur décrits dans le brief sont navigables.

Ce que ce n'est PAS : Playwright/E2E complet (c'est Sprint 6), déploiement Vercel (Sprint 6).

Ce que c'est :

User Journey Spec — l'Architect extrait non seulement les requirements (fichiers/modèles) mais aussi les user_flows (ex : "utilisateur crée un post → le publie → le lit sur /blog/[slug]")
Journey Validator — script qui vérifie que chaque étape du user_flow a une route générée correspondante dans combined_files
Seuil de valeur — spec_coverage > 80% ET user_flows_covered > 60% = "app utile"
Cela reste un script déterministe (pas un agent), mais il mesure la valeur perçue et pas juste la compilation.

