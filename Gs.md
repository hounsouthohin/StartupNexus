Compris. Tu veux définir le périmètre complet du prochain batch — les 6 fixes + certains Gs — de façon à ce que le run suivant soit testable sur les 4 dimensions (structurelle, code, sémantique, E2E/usage). On planifie d'abord, on implémente ensuite.

Voici ma lecture des 4 dimensions et ce qui manque actuellement :

Ce que les 6 fixes couvrent déjà
Fix	Dimension couverte
A1-A3 (env, prisma config, .env.example)	Infrastructure — l'app démarre sans intervention
B1 (navigation generator)	Usage — l'app est navigable
C1 (supprimer as any)	Code qualité
D1 (journey validator)	Métrique — mesure correcte de la couverture
Ce qui reste absent après les 6 fixes :

Structurelle → blueprint validator existe, mais pas de vérification que le contenu des pages correspond au brief (ex: formulaire créé, bouton delete présent)
Code → tsc passe, mais test_files_count: 0 (G6) — les tests ne tournent jamais
Sémantique → aucune review qui vérifie l'intention métier (G5 absent)
Usage/E2E → néant — aucune validation comportementale
Proposition pour compléter le batch
G5 (version minimale) — Semantic Code Scanner :
Pas une IA, un analyseur déterministe Python qui scanne les fichiers générés et vérifie :

Chaque page create a un <form
Chaque page list a au moins une référence à l'action deleteXxx
Les champs FK utilisent <select (pas <input type="text") → Résultat : semantic_score dans les métriques, violations listées
G6 (version minimale) — Tests qui tournent :
Actuellement test_files_count: 0. Le template de test middleware.test.ts existe mais les tests de business logic ne sont jamais générés. Un générateur de tests structurels (smoke tests déterministes — vérifient que chaque page export default une fonction) suffit pour avoir un signal.
→ Résultat : tests_passed: true possible

E2E — hors scope pour l'instant :
L'E2E complet (Playwright, Cypress) nécessite un app déployée avec une vraie DB — incompatible avec la livraison "code brut sans déploiement". On le garde pour plus tard (niveau 3 dans le roadmap).

Batch proposé
Groupe	Items	Dimension
A	A1, A2, A3	Infrastructure
B	B1 (navigation)	Usage
C	C1 (typage)	Code
D	D1 (journey validator)	Métrique
E	G5 mini (semantic scanner déterministe)	Sémantique
F	G6 mini (test generator — smoke tests)	Code/Tests
Est-ce que ce périmètre correspond à ce que tu vises ? Ou tu veux inclure d'autres Gs, ou exclure G5/G6 de ce batch ?



