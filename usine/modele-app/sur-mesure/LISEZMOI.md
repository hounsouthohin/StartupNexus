# Sur-mesure

Ce dossier accueille le code propre à CE client (ce que l'usine ne sait pas faire : « hors stock »).
**L'usine ne le touche jamais** : il survit à chaque nouvelle fabrication de l'app.

Le reste de l'app se divise en deux :
- le **squelette fixe** (`app/`, `components/`, `lib/` sauf `notice.ts` et `droits.ts`) — écrit et
  testé une fois pour toutes les apps ; ne pas le modifier ici ;
- les **fichiers produits** par l'usine (`zenstack/schema.zmodel`, `lib/notice.ts`, `lib/droits.ts`,
  `depart.json`) — régénérés à chaque fabrication ; ne pas les modifier ici non plus.
