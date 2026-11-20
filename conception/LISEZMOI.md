# Les dossiers de conception (depuis le 13 novembre 2026)

**Pourquoi.** Arthur ne relit pas le code ligne par ligne. Chaque pièce de l'usine est d'abord décrite dans un **dossier**
écrit en français simple ; l'autre agent le vérifie ; on ne développe qu'après la décision d'Arthur. Une fois le travail
fini, le même dossier reçoit son **compte rendu**, avec les preuves.
C'est la règle de l'usine appliquée à l'usine elle-même : celui qui construit ne se juge pas.

**Les fichiers.**
- `MODELE-DOSSIER.md` : le plan de chaque dossier (avant, relecture, après).
- `CONSIGNE-RELECTEUR.md` : le texte à coller dans Claude en ligne avec le dossier.
- `<nom-parlant>.md` : un dossier par pièce (ex. `montee-nextjs.md`, `essai-boite.md`). Pas de numéros dans les
  noms : Arthur ne s'en souvient pas, et ils gênent la compréhension. Chaque dossier se lit **seul** : il redonne le
  contexte nécessaire, pour être recopié tel quel au relecteur. Il commence par « En mots simples ».
- `../conception-technique.md` reste la carte d'ensemble. On la met à jour quand un dossier change la conception.

**Le cycle.**
1. L'**auteur**, l'un des deux agents désigné par Arthur ou proposé dans un fil, écrit la partie **Avant** du dossier.
2. L'autre agent, **vérificateur**, relit le dossier avant le code et écrit ses constats dans le fil. Claude en ligne
   est facultatif ; `CONSIGNE-RELECTEUR.md` peut servir pour une relecture extérieure.
3. L'auteur répond point par point dans la partie **Relecture** : accepté, ou refusé avec la raison. Il corrige le
   dossier.
4. **Arthur décide** : « go », ou non.
5. L'auteur développe : la preuve d'abord, puis le code, en restant dans la taille annoncée. S'il la dépasse, il
   s'arrête et rend compte.
6. L'auteur écrit la partie **Après** :
   - ce qui a été fait, les écarts et les preuves ;
   - **comment ça marche et comment c'est fait**, en mots simples ;
   - ce qu'Arthur peut voir lui-même ;
   - **ce que ça change pour la suite** : les tâches à réviser, et si une relecture extérieure est utile.
   Il le redit en quelques lignes dans la conversation, et **met à jour la carte visuelle**
   (`carte-de-l-usine.html`, publiée sur https://claude.ai/artifact/8ynHYQ1riEst6F4FjhJEYh).
7. Le vérificateur vérifie les preuves après, en les rejouant si besoin. Pour un juge, la vérification par l'autre
   fournisseur est obligatoire.
8. Arthur clôt le dossier.

**Proportionné, pour ne pas tourner sans fin.**

| Taille | Exemples | Dossier | Vérification par l'autre agent |
|---|---|---|---|
| **Petit** | montée de version corrective, petite correction de classe, outil de confort | parties Avant et Après courtes | **facultative** : Arthur valide seul, ou demande une vérification |
| **Moyen** | essai jetable, outil de mesure | complet | dossier avant **et** preuves après, dans le même fil (décision d'Arthur du 19 nov : c'est la vérification après coup qui a démasqué le « 51/51 » de l'essai du juge d'écrans) |
| **Critique** | juges, boîte, droits, orchestrateur, assembleur, capacités, sécurité | complet ; pour un juge, son code est joint à la partie Après | dossier avant et preuves après ; pour un juge, autre fournisseur obligatoire |

Trois règles d'arrêt :
- **un fil de vérification**, avec les positions et trois tours au plus ; une correction de fait, une réponse à une
  question de fait et la vérification d'une correction demandée ne comptent pas comme des tours. Un risque bloquant
  nouveau peut toujours être signalé à Arthur en une ligne ;
- **seuls les points BLOQUANTS empêchent de développer**. Les points « à corriger » se font pendant le développement.
  Les suggestions vont au registre des inconnues ou attendent ;
- le relecteur **juge le dossier**. Il ne refait ni la vision ni le plan.

**Ce qu'un dossier ne contient jamais** : une clé ou un mot de passe, une donnée de client, le contenu du lot d'examen.

**Une limite à connaître.** Même de deux fournisseurs, les agents peuvent partager des angles morts. Pour les juges,
la vérification par l'autre fournisseur est obligatoire. **Ce sont les preuves (sabotages, témoins, seuils écrits
d'avance) qui font foi, pas les avis.**
