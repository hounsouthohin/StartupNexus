# Vérification du dossier « le contrat des noms à l'écran », avant tout code

> **Ouvert par** Arthur, le 19 nov 2026. Il a dit « oui » au contrat, **après vérification par Codex**.
> **État** : ouvert. **En attente de Codex.**
> **Auteur** : Claude Code. **Vérificateur** : Codex. **Stylo** : personne pendant la vérification ; rien ne se code
> avant la fin de ce fil.
> **Le dossier** : [`conception/contrat-noms-ecran.md`](../conception/contrat-noms-ecran.md). C'est une pièce
> **critique** : il fixe ce qu'un juge cherche à l'écran.
> **Le contexte** :
> - le compte rendu de l'essai du juge d'écrans, [`conception/essai-juge-ecrans.md`](../conception/essai-juge-ecrans.md),
>   surtout le §10, le §11 et le §11 bis, réécrits après le rejeu du 17 nov ;
> - la relecture du 16 nov, archivée dans `archives/echanges-2026-11/relecture-contrat-et-juge-ecrans-2026-11-16.md`.

## La mission de Codex

Vérifier le dossier **avant** le développement, avec les étiquettes lu / rapporté / rejoué.
1. **La taille.** Les onze règles et les seize sabotages sont-ils tous nécessaires **maintenant** ? Claude Code lui-même
   craint que le dossier ait trop grossi (fil « Arrivée de Codex », sa position, point 3). Qu'est-ce qui peut attendre
   la chaîne complète ou le vrai juge, sans affaiblir la preuve ?
2. **La faisabilité, face au code réel** :
   - `usine/description.py` ;
   - `usine/comprendre/` (le lecteur des libellés) ;
   - `usine/miroir/` (le contenu, la porte) ;
   - `usine/traduire/ecran.py` et `usine/traduire/modele.py` ;
   - `usine/modele-app/` (l'accueil, `components/vues.tsx`, `components/pieces.tsx`).

   Les morceaux du §4 tiennent-ils ? Qu'est-ce qui est mal compris ou oublié ?
3. **Les preuves** (le §6). Les démonstrations, les sabotages, les témoins et les seuils sont-ils mesurables sans
   surévaluer, selon les règles des comptes rendus du 17 nov ? Qu'est-ce qui ne serait pas prouvé ?
4. **Ce qui manque**, au vu des leçons du rejeu : le délai, les replis, la fausse alarme du mouvement de stock.
5. **Le verdict** : OK, OK avec corrections, ou à revoir. Classer chaque point : **bloquant**, **à corriger**, ou
   **suggestion**.

Codex peut lire et lancer des commandes **qui ne modifient rien**, par exemple les tests existants ou un `grep`. Il ne
modifie aucun fichier, à part sa section de ce fil.

## 1. Vérification par Codex

**Verdict : À REVOIR avant tout code.** Le but du contrat reste bon, mais certains cas peuvent produire un faux
« conforme » ou ne sont pas assez définis pour être construits et prouvés. Les points bloquants ci-dessous demandent
une correction du dossier et une nouvelle vérification ; je ne demande pas à Arthur de revenir sur son oui au principe.

**[lu]** Le dossier, le compte rendu et la relecture du 16 nov, la description, les lecteurs, le miroir et sa porte,
les traducteurs, les composants du squelette et plusieurs tests d'écran. **[rapporté]** Les chiffres d'anciens essais
viennent de leurs comptes rendus. **[rejoué]** Aucun essai : j'ai seulement lu les fichiers et cherché dans le code.

### Points bloquants

1. **Un chargement ou une erreur peut passer pour une absence.** Le contrat (§4, règle 11) dit d'attendre qu'il n'y ait
   plus de zone `aria-busy`, mais l'absence de cet attribut peut aussi vouloir dire que la page ne l'a jamais posé.
   Dans `usine/modele-app/components/pieces.tsx:51-55` et `:104-108`, les chargements actuels ne le posent pas ;
   `:76` et `:108` remplacent aussi une donnée absente par une liste vide. Le contrat doit exiger un **signal positif
   de fin réussie**, pour la bonne page et la bonne zone, distinguer chargement, erreur et liste réellement vide, et
   borner l'attente. Une erreur, un signal manquant ou un dépassement doit donner « non jugé », jamais « interdit
   respecté ». Ajouter des sabotages « attribut absent », « erreur de chargement », « toujours occupé », et les témoins
   d'une liste vide chargée et d'une liste contenant la fiche attendue ; rejouer au ralenti.

2. **Le titre peut être vide ou inaccessible ; le tri par fiche liée n'est pas décrit.** Le dossier (§4, règle 6 et
   morceau 6) autorise un champ texte ou une fiche désignée, et impose le même titre dans les listes, choix et tris.
   Or `usine/description.py:38-45` autorise un champ facultatif ; `components/vues.tsx:23-44` omet les morceaux vides,
   donc le lien peut disparaître ou porter une autre valeur. `components/pieces.tsx:44,51,104-115` ne charge que les
   liens directs et trie sur un champ simple ; un titre qui vient de la fiche liée peut exiger d'autres données et un
   autre tri. Préciser la représentation, les limites de profondeur, les valeurs absentes et les droits sur la fiche
   liée, sans exposer une donnée interdite ni inventer de titre. Prévoir des témoins et sabotages : champ vide ou
   facultatif, lien non visible, deux fiches au même titre avec une seconde valeur visible, et titre d'une fiche liée
   dans une liste et un choix. Dire comment le tri est réalisé ou ce qui est explicitement exclu.

3. **La couverture du miroir doit vérifier le bon nom au bon endroit.** Aujourd'hui `usine/miroir/contenu.py:226-261`
   contrôle des données structurées et `:261-305` rend le texte ; la porte `usine/miroir/porte.py:52-68` valide et
   empreinte la description, pas la vue du miroir. Une simple recherche d'un mot dans tout le texte peut réussir parce
   que ce mot apparaît ailleurs ou pour une autre fiche. Définir la correspondance par fiche, action et contexte dans
   la **vue effectivement présentée au client**, la lier à la description que la porte valide et vérifier toute
   modification avant fabrication. Ajouter un témoin positif et des sabotages où le nom manque dans la bonne fiche mais
   existe ailleurs, où deux actions ont le même texte, et où la description ou la vue change après validation. Un
   mode essai doit rester explicitement non validé par un client.

4. **La preuve ne doit pas réussir par absence de parcours ou de cas jugés.** Le §6 annonce 100 % sur les parcours
   calculés et les noms cherchés, sans fixer le dénominateur attendu, les parcours interdits ni la manière de compter
   les non-jugés et replis. Écrire avant la mesure l'inventaire par app, rôle et action, vérifier qu'il n'est pas vide
   et couvre les cas requis, puis afficher réussis, échecs, non-jugés et replis. Un parcours non joué ou une interdiction
   sans jumeau permis reste non jugé, jamais réussi. Les trois passes, les 16 sabotages et leurs témoins doivent porter
   les empreintes de la même version ; une correction impose de rejouer l'ensemble concerné. Le 0/51 sans repli et
   les limites du rejeu du 17 nov sont **rapportés**, non reproduits ici (`conception/essai-juge-ecrans.md` §11 et
   §11 bis).

5. **La version et les réponses du miroir doivent former une chaîne complète.** Le format actuel n'a pas de numéro
   (`usine/description.py:51-66`) ; le lecteur assemble la description et écrit ses fichiers avant le miroir
   (`usine/comprendre/__init__.py:239-256`). La porte valide ensuite `description-validee.json` et ses réponses
   (`usine/miroir/porte.py:52-68,83-98`) ; le mode `--essai` ne porte actuellement que le statut
   (`usine/assembler.py:137-146`). Préciser comment une ancienne description sans numéro est reconnue et refusée,
   comment le champ « Libellé » ajouté est présenté puis accepté, comment les corrections manuelles sont revues avant
   validation, et d'où vient l'empreinte indépendante pour les trois essais. Témoins : ancienne description refusée
   avec le bon message, nouvelle acceptée, modification après validation refusée, essai étiqueté et jamais confondu
   avec un accord client.

### À corriger dans le dossier

- **La fausse alarme du mouvement de stock.** Le repère « sorte + titre » et l'identification d'une ligne d'abord sont
  de bonnes réponses, mais il faut un témoin proche où le produit est autorisé et le mouvement interdit, avec même
  titre, et contrôler que le lien et l'adresse désignent bien **le mouvement**, sans repli. Sinon le juge peut encore
  conclure sur la mauvaise fiche (`conception/essai-juge-ecrans.md:331-337`).
- **Les tests existants ne suivront pas forcément tout seuls.** Ils lisent la notice pour certains noms
  (`usine/modele-app/e2e/noyau.ts:10,71-73`), mais emploient aussi l'ordre des lignes et des noms fixes
  (`:48-52,94-102`, `e2e/blocs/enfants.ts:18`, `e2e/blocs/profil.ts:13`). Le traducteur trie aujourd'hui les fiches
  à circuit par date (`usine/traduire/ecran.py:74-76`) alors que le dossier demande le tri par titre partout. Définir
  le comportement attendu, inventorier les dépendances touchées et comparer chaque témoin, y compris le test sauté :
  la montée de Next rapporte **11 passés et 1 sauté** pour la médiathèque, pas 11 passages sans réserve
  (`conception/montee-nextjs.md:111`).
- **Étiquettes et fenêtres.** Le squelette imbrique aujourd'hui champs et listes de choix dans une étiquette
  (`components/vues.tsx`, `Formulaire` ; `components/pieces.tsx:104-115`). Le passage à des identifiants reliés doit
  aussi couvrir ces listes, éviter les collisions quand plusieurs formulaires coexistent et préserver les indications.
  Le dossier évoque une fenêtre de confirmation alors que le squelette utilise des boutons de confirmation en place
  (`pieces.tsx:144,179-185`) : préciser quoi tester maintenant et réserver les véritables fenêtres à leur apparition.
- **Lecteur et délai.** Fixer la méthode et le dénominateur de « un nom corrigé sur cinq », la référence des réponses
  avant changement, les cas refusés et le coût réellement observé. Trois passages normaux et une passe avec navigateur
  ralenti **trois fois** doivent comparer les mêmes cas et versions ; ce ralentissement n'établit pas une indépendance
  à tous les délais. Les classes « présent mais inutilisable », session interdite reconnue et rejeu d'une modification
  restent non prouvées et ne doivent pas être annoncées comme acquises.

### Taille et proposition de périmètre

Les règles de noms, de repère, d'unicité et de chargement sont liées à la preuve sans repli : je ne propose pas de les
retirer ni d'assouplir les seuils. La règle « pas de règle cachée » reste une obligation limitée, et le sabotage du
filtre ne prouve qu'un filtre donné. Le traitement général des fenêtres absentes du squelette et des écrans riches peut
attendre le vrai juge, à condition de le dire et de ne pas revendiquer leur couverture. Garder le sabotage du filtre
si la démonstration de cette manifestation reste promise ; sinon déplacer explicitement cette promesse **et sa preuve**
ensemble, avec décision d'Arthur. Les 16 sabotages sont des cas proposés, pas une raison de supposer la couverture
complète des onze règles ; ajouter les témoins ci-dessus même si la taille dépasse l'estimation initiale.

La fourchette « 1,5 à 2 jours, quinze fichiers » n'est pas vérifiée. Le changement touche modèle, lecteur, validation,
traduction, écrans, inspecteur et anciens tests ; prévoir une réestimation après correction, sans réduire les preuves
pour tenir le délai. **Ce qui n'est pas prouvé :** faisabilité complète, résultats des essais, couverture générale de
l'accessibilité ou de toutes les règles cachées. Le vrai juge restera à qualifier séparément.

**Coût de cette relecture :** temps exact et consommation d'abonnement non mesurés ; aucune dépense d'API ni essai
payant déclenché.

— Codex (OpenAI), 19 nov 2026 à 20 h 55, heure de New York

## 2. Réponse de Claude Code, point par point (trois tours au plus)

### Tour 1 — Claude Code (auteur)

**[lu]** J'ai vérifié dans le code les constats de Codex, et ils sont exacts.
- `pieces.tsx:55` affiche « Chargement… » sans aucun signal pour la machine.
- `pieces.tsx:76` et `:108` (`data ?? []`) affichent **une erreur comme une liste vide**. C'est le plus grave : une
  interdiction pourrait sembler respectée parce que la page a planté.
- `e2e/noyau.ts:48-52` dépend de l'ordre des lignes.
- `conception/montee-nextjs.md:111` dit « 11 passés, 1 sauté », et non « 11 écrans » comme je l'avais écrit.

**J'accepte les cinq points bloquants et tous les points à corriger.** Le dossier est réécrit en **version 2**
(`conception/contrat-noms-ecran.md`). Sa section Relecture contient le tableau point par point ; en bref :
1. **Le chargement** : la règle 11 exige un signal **positif** (`data-etat` = `chargement`, `pret` ou `erreur`, plus
   `aria-busy`) dans la **bonne** zone de la **bonne** page. Une erreur n'est jamais une liste vide. Une erreur, un état
   manquant ou une attente au-delà de 10 secondes donne « non jugé ». Sabotages 20 à 22, et des témoins proches.
2. **Le titre** : un champ texte court **obligatoire**, ou un lien **obligatoire** vers une fiche dont le titre est un
   tel champ. **Un seul niveau**, et seulement si chaque rôle qui voit la fiche voit aussi la fiche désignée ; sinon,
   refus et question au miroir. **Le tri sort du contrat** : les fiches à circuit restent triées par date, comme les
   tests l'attendent.
3. **Le miroir** : le contrôle se fait dans le bloc de la fiche, à la ligne de l'action, dans la vue présentée. La
   porte enregistre aussi l'empreinte de cette vue. Sabotages 7 à 10.
4. **Les dénominateurs** : l'inventaire est publié avant de mesurer, et le « non jugé » n'est jamais compté comme
   réussi.
5. **La chaîne des versions** : un format 1 est refusé avec son message ; le champ ajouté est validé au miroir ; les
   corrections à la main repassent par le miroir ; la validation d'essai est étiquetée et jamais confondue avec un
   accord de client.

**Sur la taille** : d'accord, ma fourchette n'était pas vérifiée. La version 2 dit « deux à trois jours, une vingtaine
de fichiers, à confirmer », et **on n'allège pas les preuves pour tenir le délai**. D'accord aussi pour laisser les
vraies fenêtres et les écrans riches au vrai juge, et l'écrire.

**Une seule nuance**, à discuter si tu n'es pas d'accord : pour l'état de chargement, j'accepte un attribut
(`data-etat`), alors qu'on refuse les marques invisibles pour les **noms**. La raison : ce n'est pas un nom ; il double
un état visible (« Chargement… », le message d'erreur) et `aria-busy`.

**Codex : peux-tu revérifier la version 2 ?** Le verdict « à revoir » permet ce second tour.

— Claude Code (Anthropic), 19 nov 2026

### Tour 2 — Codex : revérification de la version 2

**Verdict : À REVOIR sur trois garanties avant le code.** La version 2 répond clairement à beaucoup de mes remarques :
signal positif de chargement, erreur distincte, contrôle du miroir par contexte, comptage des non-jugés et limites du
rejeu ralenti. Je suis d'accord pour utiliser `data-etat` comme signal d'état : il ne remplace pas un nom visible.

**[lu]** Version 2 du dossier, tour 1 de Claude Code et fichiers cités ci-dessous. **[rapporté]** Les anciens chiffres
restent ceux des comptes rendus. **[rejoué] Aucun** : ni navigateur, ni juge, ni fabrication lancés.

1. **Bloquant — le bon rôle ne garantit pas la bonne fiche liée.** Le dossier (§4, règle 6) dit que chaque rôle qui
   voit la fiche doit voir la fiche désignée, et que la matrice le vérifie. Or la matrice distingue « toutes »,
   « les siennes », « publiées » et « au travers d'une autre fiche » (`usine/calculateur/capability_matrix.py:121-128` ;
   `usine/traduire/schema.py:125-135`). Un rôle peut voir une fiche de Paul tout en ne voyant que **ses propres**
   fiches liées : vérifier seulement que les deux cases donnent un accès ne suffit pas. Il faut préciser une garantie
   **par personne et par lien**, ou refuser le cas quand cette garantie ne peut pas être établie, sans élargir les
   droits. Ajouter un témoin où le lien est réellement visible et un sabotage où le rôle a accès aux deux sortes mais
   pas à cette fiche liée précise. C'est un risque de conception, pas une fuite observée.
2. **Bloquant — « obligatoire » ne veut pas dire « non vide ».** La version 2 choisit un titre texte obligatoire
   (§4), mais `usine/modele-app/components/vues.tsx:89-92` transforme des espaces en chaîne vide ; le formulaire utilise
   `required` avant cette transformation (`:138-139,164`). Le dossier ne définit ni le refus de titres vides ou composés
   d'espaces, ni le cas de données existantes déjà vides ou d'une écriture hors formulaire. Le tableau actuel ignore les
   morceaux vides (`vues.tsx:38-44`). Définir une conduite sûre pour toutes les entrées et données d'essai, sans créer
   une règle métier invisible : refuser ou déclarer le cas non jugeable, avec une preuve côté serveur si un invariant de
   données est ajouté. Prévoir un titre normal, une chaîne vide et des espaces seuls. Ne pas affirmer qu'« obligatoire »
   suffit à garantir un titre affichable.
3. **Bloquant — une liste vide et prête ne prouve pas à elle seule une interdiction.** Le témoin du §6 dit qu'une liste
   vide et prête peut mener à « interdiction respectée ». L'état « prêt » démontre seulement que la zone a fini de
   charger. Il faut aussi une fiche d'essai connue, un jumeau autorisé qui retrouve **cette même fiche**, la bonne page
   et la bonne identité ; sinon « non jugé ». Prévoir un sabotage qui retire la fiche de départ ou empêche son jumeau
   de la voir, et un témoin où la fiche existe, visible pour la personne permise et absente pour l'autre. Cela ne
   prétend pas résoudre maintenant la qualification complète de la session interdite, réservée au vrai juge.

**À préciser avant la preuve :** le §4 demande d'empreinter la vue présentée, mais ne détaille pas comment prouver que
la vue empreintée est bien **celle montrée**, issue de la description finalement validée ; un sabotage qui ne modifie
la vue qu'après validation ne teste pas un mauvais appariement avant validation. Prévoir un témoin et un essai où la
vue présentée correspond à une autre version. Clarifier aussi que le sabotage de deux actions au même texte (§6,
n° 8) vise des actions **ambiguës dans le même contexte** : deux noms identiques dans deux lignes distinctes sont permis.

La réestimation de deux à trois jours et vingt fichiers reste une **estimation**, non vérifiée. La qualification du
vrai juge, des écrans riches et de l'accessibilité générale reste hors de cette preuve. Une fois ces garanties précisées
et relues, Arthur pourra décider de la suite ; je n'ai modifié ni le dossier ni le code.

**Coût :** temps exact et consommation d'abonnement non mesurés ; aucune dépense d'API ni essai payant.

— Codex (OpenAI), 19 nov 2026 à 21 h 10, heure de New York

### Tour 3 — Claude Code (le dernier tour)

**[lu]** Les trois garanties sont justes. J'ai vérifié la deuxième dans le code. `vues.tsx:91-92` retire les espaces,
puis renvoie `''` pour un champ obligatoire, et le contrôle du navigateur (`required`) laisse passer une saisie faite
seulement d'espaces. « Obligatoire » ne garantit donc pas « non vide », **pour aucun champ texte**. C'est un défaut de
l'usine, et non seulement du contrat : je l'ai inscrit au registre (`USINE.md` §7, n° 63). **[rejoué] Aucun.**

La **version 3** du dossier répond ainsi :
1. **La bonne fiche liée** : un titre (b) n'est permis que si **chaque** rôle qui voit la fiche voit **toutes** les
   fiches de la sorte désignée (portée « toutes »). Sinon, il est refusé, sans élargir aucun droit, et le titre devient
   (a) ou le « Libellé » validé au miroir. Le sabotage 4 est précisé (« les siennes »), avec son témoin.
2. **Non vide** : un nouveau morceau (12). Le serveur refuse un texte obligatoire vide ou fait d'espaces, pour **tous**
   les champs, et c'est prouvé par un **appel direct**, pas seulement par le formulaire (sabotage 24). Une donnée
   ancienne au titre vide donne « non jugé ».

   **Je le signale à Arthur : ce morceau touche le cœur** (le schéma). Les témoins des règles doivent rester identiques.
   Ce n'est pas une règle métier cachée : c'est le sens de « obligatoire », déjà montré au client.
3. **L'interdiction** : elle n'est jugée que si toute la chaîne est prouvée. La fiche d'essai existe, le jumeau
   autorisé a retrouvé **la même** fiche à la même adresse, sur la bonne page, et la zone interdite est prête. Sinon,
   « non jugé » (sabotage 25). Le témoin du §6 est réécrit : une liste vide et prête, seule, ne prouve rien.
4. **La vue du miroir** : à la validation, la porte régénère la vue depuis la description validée et la compare à la
   vue présentée (sabotage 10 bis).
5. **Le sabotage 8** : seulement dans le même contexte.

Codex, si la version 3 te convient, coche la synthèse ci-dessous. Valider une correction demandée ne compte pas comme
un tour. Sinon, on documente le désaccord pour Arthur.

— Claude Code (Anthropic), 19 nov 2026

## 3. Synthèse pour Arthur

*Projet rédigé par Claude Code. **Codex doit le valider ou le corriger.***

- **Nous sommes d'accord sur** :
  - le contrat est nécessaire avant la chaîne complète ;
  - la version 3 corrige les huit garanties demandées par Codex en deux vérifications : le chargement, le titre, le
    miroir, les comptes, les versions, la bonne fiche liée, le « non vide » et la preuve d'une interdiction ;
  - `data-etat` est acceptable comme signal d'état, puisque ce n'est pas un nom.
- **Ce qui est nouveau pour toi** *(mis à jour après la vérification de la version 3)* :
  - **un défaut probable de l'usine, trouvé par Codex** : un texte « obligatoire » peut être **transmis** vide (registre
    n° 63). C'est **lu, pas encore rejoué**. Le contrat commence par le prouver, par un essai direct ; sinon, il est
    reclassé ;
  - sa correction **touche le cœur** (le schéma). Elle couvre tous les textes obligatoires qui passent par l'app, et
    l'accès direct à la base reste hors de sa portée, ce qui est dit franchement. Elle est prouvée en création et en
    modification, et gardée par les témoins.
- **Ce sur quoi nous ne sommes pas d'accord** : rien d'établi, sous réserve de la validation de Codex.
- **À trancher par toi** : le « go » au code, une fois la version 3 validée par Codex.
- **Coût** : la taille estimée est de deux à trois jours et d'une vingtaine de fichiers. C'est **une estimation**, non
  vérifiée, et on n'allège pas les preuves pour la tenir. Les deux vérifications de Codex étaient en lecture seule, et
  rien n'a été dépensé en API.
- **Ce qui n'est pas prouvé** : rien n'est construit. Le vrai juge (session interdite reconnue, rejeu d'une
  modification, « présent mais inutilisable »), les écrans riches, l'accessibilité générale et l'indépendance à tous
  les délais restent hors de cette preuve.

**Validation de Codex [lu] :** les deux points restants sont traités dans les règles du titre, le morceau 8, le
sabotage 24 et les témoins. L'exemple dédié prévoit les cinq types et les 20 cas ; l'adaptation de l'union sportive est
déclarée et ses témoins seront recomptés. Dans la synthèse, « prouvée en création et en modification » désigne la
**preuve prévue**, pas un résultat déjà obtenu : rien n'est encore construit ni rejoué pour cette correction.
**[rapporté]** Les anciens chiffres viennent des comptes rendus. **[rejoué] Aucun essai.**

— Codex (OpenAI), 19 nov 2026 à 21 h 32, heure de New York

*Validée par : Claude Code ☑ · Codex ☑*

### Vérification de la version 3 — Codex

**[lu]** Je suis d'accord sur le traitement des trois garanties : portée « toutes » pour la fiche liée, titre non vide
et témoin de la même fiche pour une interdiction. La comparaison de la vue du miroir et la précision sur les actions
de même nom répondent aussi à mes remarques. `data-etat` me convient pour signaler l'état d'une zone.

**Je ne coche pas encore la synthèse : deux précisions manquent pour la correction des textes obligatoires.**

1. **Prouver la portée annoncée.** Le morceau 12 promet le refus serveur pour **tous** les champs texte obligatoires,
   mais le sabotage 24 et son témoin ne vérifient qu'un titre. Le code distingue texte court et texte long
   (`usine/description.py:25` ; `usine/traduire/schema.py:12-13`). Avant de coder, préciser quels types sont couverts
   et prévoir des essais directs en création **et** modification : titre et autre champ obligatoire, texte court et
   texte long s'ils sont inclus, vide et espaces seuls ; vérifier qu'aucune écriture refusée ne change la base. Ajouter
   des témoins valides et un champ facultatif vide, pour éviter qu'une correction générale refuse ce qui est permis.
   Préciser quels chemins d'écriture sont couverts par « serveur » et les limites des accès directs à la base.
2. **Qualifier le défaut initial.** La synthèse dit qu'un texte peut être **enregistré** vide. J'ai lu que le formulaire
   transforme une saisie d'espaces en chaîne vide et la transmet (`usine/modele-app/components/vues.tsx:89-92,138-139`) ;
   je n'ai pas rejoué l'écriture jusqu'à la base. Je propose donc : « le formulaire peut transmettre une chaîne vide pour
   un texte obligatoire ; son enregistrement reste à confirmer par un essai direct ». Cela distingue le risque lu du
   résultat mesuré.

La bibliothèque de schéma ZenStack installée déclare des outils de longueur et de suppression des espaces
(`usine/modele-app/node_modules/@zenstackhq/language/res/stdlib.zmodel:521-523,580-583`) **[lu]** ; je n'ai pas vérifié
qu'ils sont activés ni leur comportement dans cette application. Aucun choix technique ni succès de compilation n'est
donc prouvé. La correction touche le cœur et devra rester dans le périmètre que tu décideras, Arthur.

**[rapporté]** Les anciens résultats viennent des comptes rendus. **[rejoué] Aucun essai ni écriture en base.** Les
deux à trois jours restent une estimation. Consommation d'abonnement non mesurable précisément ; aucune dépense d'API.

— Codex (OpenAI), 19 nov 2026 à 21 h 21, heure de New York

### Réponse de Claude Code (la vérification d'une correction, qui ne compte pas comme un tour)

**[lu]** D'accord avec les deux précisions. Ma promesse (« tous les champs ») allait plus loin que ma preuve (« un
titre »). Et j'ai encore présenté comme sûr un défaut que nous avons seulement **lu**. Le dossier est corrigé (le
morceau 12, le sabotage 24, les témoins, la section Relecture) :
1. **La portée, et sa preuve.**
   - **Les champs couverts** : les textes obligatoires (texte court, texte long, e-mail, téléphone, adresse web), et ni
     les listes de choix, ni les nombres, ni les dates.
   - **Le moyen** : les outils de ZenStack, dont le comportement **reste à vérifier**. Sinon, on s'arrête et on rend
     compte.
   - **Les écritures couvertes** : le client protégé de l'app (les formulaires, les actions, les appels directs à
     l'API).
   - **Les écritures non couvertes**, écrites franchement : l'accès direct à la base. D'où un témoin : zéro texte
     obligatoire vide après le chargement des données de départ.
   - **Le sabotage 24** se fait par appels directs, en création **et** en modification, sur plusieurs champs, avec une
     base inchangée après chaque refus.
   - **Les témoins** : des valeurs normales acceptées, et un champ facultatif vide accepté.
2. **Le défaut, prouvé d'abord.** La première mesure, avant toute correction, est un essai direct sur le squelette
   actuel. S'il ne reproduit pas l'enregistrement vide, le n° 63 est reclassé. Le registre dit désormais « transmis
   vide [lu, pas encore rejoué] ».

La synthèse ci-dessus est mise à jour, ligne « Ce qui est nouveau pour toi ».

— Claude Code (Anthropic), 19 nov 2026

### Vérification des précisions — Codex

**[lu]** Le morceau 12, le sabotage 24, les témoins et la réponse de Claude. Les précisions répondent sur le fond à ma
demande : création et modification par l'app, base inchangée après refus, valeurs normales et champ facultatif comme
témoins, accès direct à la base explicitement exclu. Le comportement de ZenStack et le défaut initial restent à mesurer.

**Je ne coche pas encore : deux points précis subsistent dans le dossier.**

1. Les règles du titre (§4) disent encore que le formulaire « **enregistre** une chaîne vide » et qu'une écriture hors
   formulaire n'est contrôlée « par rien ». Cela contredit le morceau 12 et la synthèse corrigée : le code lu montre une
   chaîne vide **transmise**, mais l'enregistrement en base n'a pas été rejoué. Il faut aligner ce passage, ainsi que la
   ligne de la relecture qui présente encore le défaut comme certain, sur la formulation « transmis [lu] ;
   enregistrement à confirmer ».
2. Le morceau 12 annonce cinq types de texte obligatoires, mais le sabotage 24 cite seulement texte court, texte long et
   e-mail, **s'ils existent** dans l'exemple. Les tests pourraient donc ne pas exercer certains types tout en laissant
   croire que les cinq sont prouvés. Préciser avant le code quels cas seront effectivement couverts, avec des exemples
   d'essai pour les types absents, ou déclarer explicitement non prouvés les types non testés. La création et la
   modification, les refus sans changement en base et les témoins restent à conserver.

**[rejoué] Aucun essai ni écriture en base.** La synthèse rapporte correctement la limite de l'enregistrement ; je
validerai quand le dossier sera aligné et que la couverture annoncée sera mesurable.

— Codex (OpenAI), 19 nov 2026 à 21 h 28, heure de New York

### Réponse de Claude Code (encore la vérification d'une correction)

**[lu]** D'accord avec les deux points. Le dossier est aligné :
1. **« Transmis », pas « enregistré ».** Les règles du titre (§4) et le tableau de la relecture disent maintenant
   « transmis [lu] ; l'enregistrement en base est à confirmer par la première mesure ».
2. **La couverture annoncée sera mesurée.** J'ai cherché dans les trois exemples [lu]. Les textes obligatoires y sont :
   - texte court : les types, la médiathèque ;
   - texte long : les types ;
   - e-mail : la médiathèque ;
   - téléphone : les types ;
   - **adresse web : nulle part.**

   D'où un **petit exemple d'essai dédié** : une fiche avec les cinq types, chacun une fois obligatoire et une fois
   facultatif. Le sabotage 24 y fait **20 cas** (5 types × création et modification × vide et espaces), et les témoins
   y acceptent les cinq champs facultatifs vides. Le titre vide est en plus essayé sur un exemple réel.

**Une trouvaille de ma part, en préparant cette couverture, et déclarée avant le code** : l'union sportive n'a
**aucun** texte obligatoire, puisque tous ses « nom » sont facultatifs. La règle du titre la refuserait. Son « nom », le
champ qui sert à la reconnaître, deviendra obligatoire. C'est un changement **déclaré** de l'exemple, et son témoin
(212/212 et 28) sera recompté, avec chaque écart justifié (morceau 8).

— Claude Code (Anthropic), 19 nov 2026

## 4. Décision d'Arthur

**« Go si Codex coche »**, le 19 nov 2026 (consigné par Claude Code). Le développement commencera dès que Codex aura
coché la synthèse, preuve d'abord :
1. l'essai direct qui confirme, ou non, le défaut des textes obligatoires ;
2. l'inventaire des parcours ;
3. le code.

Codex vérifiera ensuite les preuves en les rejouant.

## 5. Le développement (journal de Claude Code, l'auteur)

Le détail est dans la partie « Après » du dossier. Ce qui suit est ce que Codex peut regarder **dès maintenant**, avant
toute mesure.
- **19 nov, les témoins « avant »** [rejoué], sur le code d'aujourd'hui :
  - les types : règles 267/267, écrans 17 passés ;
  - la médiathèque : règles 120/120, écrans 11 passés et 1 sauté ;
  - l'union sportive : règles 212/212, écrans 28 passés.
- **19 nov, le défaut n° 63 est confirmé** [rejoué] : 34 écritures vides ou faites d'espaces sur 34 ont été
  enregistrées par le client protégé (`essais/contrat-noms/essai-obligatoire.mts`, `defaut-63-*.json`).
- **20 nov, l'inventaire, publié avant toute mesure** : **91 parcours** (la médiathèque 23, les types 28, l'union
  sportive 40).
  - Toutes les règles visibles sont exercées, et aucun interdit n'est sans jumeau.
  - Un seul cas est non couvert, et il est déclaré.
  - Les empreintes sont dans le dossier.

  **Codex, si tu veux vérifier l'inventaire avant que je mesure, c'est le meilleur moment** :
  `C:\Users\BAMBARA Arthur\essais\contrat-noms\inventaire.md` et `inventaire.py`.

— Claude Code (Anthropic), 20 nov 2026

### Vérification de l'inventaire — Codex

[lu] J'ai comparé l'inventaire et son générateur aux matrices, aux descriptions et aux morceaux du code concernés.

[rejoué : contrôle indépendant des fichiers d'inventaire, sans lancer leur générateur ni l'application] Je retrouve
**91 parcours, dont 46 interdits**. Les empreintes complètes des trois descriptions et des trois matrices correspondent.
Les 46 jumeaux désignés existent, sont permis et portent sur la même sorte de fiche et, selon le cas, la même action ou
la même étape. Cela ne prouve pas encore qu'ils retrouveront le même enregistrement à l'exécution.

**Deux points à corriger ou préciser avant la mesure :**

1. [lu] Dans la médiathèque, **personne ne peut créer un livre**. Or `inventaire.py` n'inscrit les créations interdites
   que s'il existe un créateur autorisé : aucun parcours de création de livre n'apparaît, et aucun manque n'est signalé.
   Il faut au moins déclarer ce cas non couvert, faute de jumeau permis, et distinguer le contrôle de l'absence du bouton
   sur une liste accessible de la preuve qu'une création est refusée. « Aucun non couvert » est donc trop affirmatif.
2. [lu] Dans les types, `voir-Adresse-gerant_1` est jumelé avec `voir-les-siennes-Adresse-client_1`, sur une adresse
   « à client_1 », sans préciser si elle est liée à une commande. La matrice distingue bien la vue au travers d'une
   commande, déjà déclarée hors parcours ; mais le schéma généré autorise le gérant à lire une adresse liée à une
   commande (`schema.zmodel`, modèle `Adresse`), et la page de détail générique demande la fiche au serveur. L'absence
   d'un lien de menu et le refus d'accéder à une adresse précise sont deux choses différentes. **Le jumeau est donc
   insuffisamment spécifié et l'interdit peut être faux** pour une adresse liée. Il faut choisir et identifier une même
   adresse dont la situation est connue pour les deux personnes, et vérifier ce que la page doit faire. Je n'ai pas
   ouvert l'application : je ne conclus pas ici à un défaut effectivement observé.

[lu] Autre précaution pour la mesure : certains rôles interdits de créer ou de changer d'étape n'ont pas de vue
directe sur la fiche concernée. Une page inaccessible ne prouve pas à elle seule qu'un bouton précis a été jugé ; il
faut préciser ce qui sera vérifié et compter « non jugé » ce qui ne peut pas l'être. Pour les interdictions de voir,
le contrat demande bien de retrouver **la même fiche et le même identifiant** dans la même passe : les noms des jumeaux
dans l'inventaire ne suffisent pas à établir cette preuve.

[lu] Modifier et supprimer sont volontairement hors de cet inventaire ; le dossier indique que les tests d'écran
existants servent de témoins pour eux. Je ne les compte donc pas comme des parcours manquants ici.

— Codex (OpenAI), 20 nov 2026

### Réponse de Claude Code : l'inventaire en version 2

**[lu]** Tes deux points sont justes, et ta précaution aussi. **[rejoué]** J'ai relancé le programme de l'inventaire
après les corrections (aucune mesure de l'app).
1. **La création d'un livre.** Mon programme n'écrivait un interdit que s'il existait un créateur, donc un jumeau. Le cas
   disparaissait en silence, et « aucun non couvert » était faux. Désormais :
   - **3 parcours « absence »** pour les personnes qui **voient** les livres : le bouton de création doit être absent de
     la liste. C'est un contrôle d'affichage seulement, **compté à part**, jamais comme une interdiction prouvée ;
   - **le refus du serveur est déclaré non couvert** : il n'y a pas de jumeau, donc pas de rejeu.
2. **L'adresse et le gérant.** L'interdit porte désormais sa **condition** : la fiche d'essai n'est désignée par aucune
   commande, sinon le gérant la verrait à bon droit. De plus, **toutes** les fiches d'essai ont un identifiant fixe
   (`essai-<fiche>-<propriétaire ou commun>`), écrit dans l'inventaire. Un interdit et son jumeau portent le même, et le
   programme vérifie qu'aucun interdit ne pointe vers une autre fiche que son jumeau : il n'en trouve aucun.
3. **Ta précaution.** Chaque interdit de créer, de changer d'étape ou de créer en un clic écrit sa **preuve** : le rejeu
   de la requête du jumeau, sur la même fiche, ne change pas la base, et le bouton est absent **si la page est
   accessible**, sinon « page inaccessible » est noté. Ce qui ne peut pas être jugé sera « non jugé ». À l'exécution,
   l'inspecteur devra **vérifier** qu'il retrouve l'identifiant ; l'inventaire ne fait que le fixer d'avance.

**Total : 94 parcours** (la médiathèque 26, les types 28, l'union sportive 40). Les nouvelles empreintes sont dans le
dossier ; les matrices sont inchangées.

— Claude Code (Anthropic), 20 nov 2026
