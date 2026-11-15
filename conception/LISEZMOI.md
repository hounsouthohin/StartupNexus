# Les dossiers de conception (depuis le 13 novembre 2026)

**Pourquoi.** Arthur ne relit pas le code ligne par ligne. Chaque pièce de l'usine est d'abord décrite dans un **dossier**
écrit en français simple ; un **relecteur extérieur** (Claude en ligne, parfois une IA d'un autre fournisseur) le juge ;
on ne développe qu'après. Une fois le travail fini, le même dossier reçoit son **compte rendu**, avec les preuves.
C'est la règle de l'usine appliquée à l'usine elle-même : celui qui construit ne se juge pas.

**Les fichiers.**
- `MODELE-DOSSIER.md` : le plan de chaque dossier (avant, relecture, après).
- `CONSIGNE-RELECTEUR.md` : le texte à coller dans Claude en ligne avec le dossier.
- `<nom-parlant>.md` : un dossier par pièce (ex. `montee-nextjs.md`, `essai-boite.md`). Pas de numéros dans les
  noms : Arthur ne s'en souvient pas, et ils gênent la compréhension. Chaque dossier se lit **seul** : il redonne le
  contexte nécessaire, pour être recopié tel quel au relecteur. Il commence par « En mots simples ».
- `../conception-technique.md` reste la carte d'ensemble. On la met à jour quand un dossier change la conception.

**Le cycle.**
1. Claude Code écrit la partie **Avant** du dossier.
2. Arthur la donne au relecteur, avec `CONSIGNE-RELECTEUR.md`, et colle sa réponse dans `sorties.md` (racine).
3. Claude Code répond point par point dans la partie **Relecture** : accepté, ou refusé avec la raison. Il corrige
   le dossier.
4. **Arthur décide** : « go », ou non.
5. Claude Code développe : la preuve d'abord, puis le code, en restant dans la taille annoncée. S'il la dépasse, il
   s'arrête et rend compte.
6. Claude Code écrit la partie **Après** : ce qui a été fait, les écarts, les preuves, et ce qu'Arthur peut voir
   lui-même.
7. Pour une pièce critique, le relecteur juge aussi la partie Après.
8. Arthur clôt le dossier.

**Proportionné, pour ne pas tourner sans fin.**

| Taille | Exemples | Dossier | Relecteur extérieur |
|---|---|---|---|
| **Petit** | montée de version corrective, petite correction de classe, outil de confort | parties Avant et Après courtes | non : Arthur valide seul |
| **Moyen** | essai jetable, outil de mesure | complet | sur la partie Avant |
| **Critique** | juges, boîte, droits, orchestrateur, assembleur, capacités, sécurité | complet ; pour un juge, son code est joint à la partie Après | sur l'Avant **et** l'Après ; pour un juge, au moins une fois par une IA d'un autre fournisseur |

Trois règles d'arrêt :
- **un seul tour de relecture** ; un second seulement si le verdict est « À REVOIR » ; ensuite, Arthur tranche ;
- **seuls les points BLOQUANTS empêchent de développer**. Les points « à corriger » se font pendant le développement.
  Les suggestions vont au registre des inconnues ou attendent ;
- le relecteur **juge le dossier**. Il ne refait ni la vision ni le plan.

**Ce qu'un dossier ne contient jamais** : une clé ou un mot de passe, une donnée de client, le contenu du lot d'examen.

**Une limite à connaître.** Claude en ligne est de la même famille que Claude Code. Ils peuvent partager les mêmes
angles morts. Pour les juges, qui sont le seul code où une erreur passe en silence, au moins une relecture se fait par
une IA d'un autre fournisseur. Et quoi qu'en dise le relecteur, **ce sont les preuves (sabotages, témoins, seuils
écrits d'avance) qui font foi, pas les avis**.
