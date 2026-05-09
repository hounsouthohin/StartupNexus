Quel chemin prend cette startup
La trajectoire est claire : expansion progressive de la couche déterministe, concentration du LLM sur les décisions purement UI.

Aujourd'hui, le LLM génère encore les pages (layout, interactions, affichage des données). À mesure que la startup monte en maturité, même cette couche se standardise : les patterns de liste, de formulaire, de détail sont répétitifs. On pourrait imaginer une "bibliothèque de patterns UI" déterministe pour les cas communs, et laisser le LLM uniquement pour les pages avec logique métier spécifique.

À maturité, la startup serait capable de :

Prendre un brief en langage naturel en entrée
Produire un projet Next.js complet, compilable, déployable sur Vercel/Railway, en 8–15 minutes
Garantir la sécurité (auth guard partout), la cohérence des types, et la couverture des cas d'erreur (notFound, loading, error boundaries)
Gérer N briefs en parallèle sans intervention humaine
Apprendre de chaque run échoué via le learner agent
Ce que cette startup serait : un compilateur de brief métier vers app web production-ready. Pas un générateur de code — un compilateur. La distinction est que la sortie est garantie correcte, pas probable correcte.