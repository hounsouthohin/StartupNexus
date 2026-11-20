# L'essai des exemples du client recueillis à l'aveugle

> **Taille** : moyen (essai jetable) · **Statut** : écrit, **à vérifier par Codex**, après le contrat des noms à l'écran
> **Dates** : écrit le 19 nov 2026 par Claude Code (auteur) · vérifié le … · validé le … · fini le …
> **Origine** : l'idée n° 1 du [regard neuf de Codex](../dialogue/2026-11-19-regard-neuf-sur-le-concept.md), décidée
> par Arthur le 19 nov. C'est l'inconnue n° 12 de `USINE.md`.

> **Règles d'écriture** : des noms, pas des codes ; des mots simples ; toujours le pourquoi.

## Avant : la conception

### 1. En mots simples

- **Ce que c'est.** Avant de montrer au client ce que l'usine a compris de sa demande, on lui pose une douzaine de
  questions concrètes : « Un membre de l'équipe peut-il voir les devis d'un autre membre ? ». Il répond **sans voir notre
  calcul**. Ensuite seulement, on compare ses réponses à ce que l'usine a calculé. Chaque différence est soit une erreur
  de l'usine, soit une question mal comprise.
- **Pourquoi.** Dans notre usine, tout découle de la description : le cœur, les écrans, les juges. Si la description a
  mal compris le client, tout est faux **de façon cohérente**, et aucun juge ne le voit, puisque les juges lisent la même
  description. Le miroir existe pour ça, mais il montre au client **notre** calcul et lui demande de confirmer. Or un
  client lit vite, et a tendance à dire oui. Les réponses à l'aveugle sont un regard indépendant : c'est notre règle des
  positions indépendantes, appliquée au client.
- **Ce qu'on verra à la fin.** Sur un brief, avec des erreurs glissées exprès dans la description, on saura :
  - combien de ces erreurs les questions à l'aveugle ont attrapées ;
  - combien le miroir seul en a attrapées ;
  - combien de fausses alarmes les questions ont produites ;
  - combien de minutes elles ajoutent.

### 2. À quoi ça sert

C'est la seule pièce de l'usine qui peut attraper « **la bonne app pour le mauvais besoin** ». Elle se place entre la
lecture du brief et le miroir. Si l'essai réussit, les exemples entrent dans le miroir. S'il échoue, le miroir reste tel
quel, et l'inconnue n° 7 (« le miroir attrape-t-il les erreurs de lecture ? ») reste ouverte.

### 3. Ce qui existe déjà

- **La lecture d'un brief** (`python -m usine comprendre`), qui écrit la description et le miroir. Ses lecteurs passent
  par la session isolée de l'abonnement, à petit volume.
- **La matrice garde l'origine de chaque droit** (`usine/calculateur/capability_matrix.py`) : la phrase du brief qui le
  justifie, ou la règle par défaut de l'usine qui l'a posé (« tient le registre », « préréglage collection »…). C'est ce
  qui permet de viser les droits **devinés**, où une erreur de compréhension est la plus probable.
- **Le miroir** (`usine/miroir/contenu.py`) : les phrases par rôle, les questions sur les cas ambigus, la porte de
  validation.
- **Rien d'autre ne mesure aujourd'hui si le client a été bien compris.**

### 4. Comment on la construit

**Le déroulé d'une séance** (environ 45 minutes avec la personne, Arthur présent) :

```
 la personne écrit son brief → l'usine le lit → on fige 12 questions → on glisse 3 erreurs (en secret)
   → ① la personne répond aux 12 questions, sans rien voir
   → ② elle lit le miroir (avec les erreurs), et le valide ou le corrige, comme d'habitude
   → ③ un programme compare ses réponses ① au calcul
   → ④ chaque différence lui est montrée : « vous avez dit X, le calcul dit Y : qu'est-ce qui est juste ? »
```

**Les choix, et pourquoi :**
1. **Le brief.** Une personne qui **ne connaît pas l'usine** écrit, en 5 à 10 lignes, un petit besoin de gestion
   qu'elle connaît : son association, un commerce, un club. Arthur la choisit.
   - *Pourquoi* : c'est le cas réel (le client parle de son propre besoin), et elle sait répondre sans réfléchir à
     l'usine.
   - *Repli* : un brief du lot d'apprentissage (`usine/briefs_reels/apprentissage/`, jamais le lot d'examen), dont elle
     joue le rôle.
   - Le brief ne contient aucune donnée personnelle, puisque les lecteurs l'envoient à l'IA. On le lui dit.
2. **Les questions viennent des noms, jamais des droits calculés.** Un petit programme fabrique les questions à partir
   des **acteurs et des fiches** de la lecture, et de gestes fixes :
   - voir ceux d'un autre ;
   - créer ;
   - modifier ceux d'un autre ;
   - faire passer d'un état à un autre.

   *Pourquoi* : si les questions venaient du calcul, elles hériteraient de l'erreur qu'elles doivent attraper.
3. **Lesquelles poser : douze.**
   - **Huit** visent des droits **devinés** par l'usine. La matrice dit d'où vient chaque droit, mais **on ne regarde
     pas sa réponse**.
   - **Quatre** sont tirées au hasard parmi les droits **cités** par le brief : ce sont les témoins.
   - Le tirage a une graine notée.

   *Pourquoi douze* : au-delà, un client se lasse (déjà constaté avec le miroir, qui a regroupé ses questions de noms).
4. **Les erreurs glissées.** **Après** avoir figé les questions, un programme change **trois** droits devinés dans la
   description, tirés au hasard, avec une graine notée.
   - Exemple : le membre de l'équipe voit maintenant **tous** les devis, au lieu des siens.
   - Les trois erreurs sont écrites dans un fichier scellé, que ni la personne ni Arthur ne lisent avant la fin.

   *Pourquoi après, et au hasard* : si on choisissait les erreurs en connaissant les questions, on mesurerait notre
   habileté, pas la méthode. *Pourquoi trois* : une seule donnerait un oui ou un non, sans aucune nuance.
5. **L'ordre : à l'aveugle d'abord, puis le miroir.** Les questions préparent la personne à mieux lire le miroir : le
   miroir est donc **avantagé** dans cette comparaison, et on l'écrit. Si les questions attrapent quand même plus
   d'erreurs que le miroir, le signal n'en est que plus fort.
6. **Le classement de chaque différence.** Il se fait avec la personne, à l'étape ④ :
   - une erreur glissée ;
   - une **vraie** erreur de lecture de l'usine (un bonus, compté à part, et inscrite au registre si c'en est une) ;
   - une question mal comprise ;
   - un changement d'avis.

**Ce qui est construit** : un essai jetable, hors du dépôt, dans `C:\Users\BAMBARA Arthur\essais\exemples-aveugle\`.
- `questions.py` : les douze questions, à partir de la description et de l'origine des droits.
- `glisser.py` : les trois erreurs, avec le fichier scellé.
- `comparer.py` : les différences, et le bilan.
- Une page simple, à imprimer ou à afficher, pour les réponses. **Rien ne change dans l'usine** avant le résultat.

### 5. Les pièges et leurs parades

- **Des questions mal tournées**, qui suggèrent la réponse. Parade : une forme fixe et neutre (« peut-il… ? », réponse
  oui / non / je ne sais pas), relue par Codex avant la séance.
- **Arthur influence la personne** : il connaît l'usine. Parade : pendant l'étape ①, il lit les questions telles
  quelles, sans commentaire.
- **La fatigue** : douze questions au plus, et le temps est noté.
- **Les erreurs glissées tombent hors des questions.** C'est voulu, puisqu'elles sont tirées au hasard. On compte combien
  étaient **couvertes** par une question, et combien ont été **attrapées**, séparément.
- **Une seule personne, un seul brief** : c'est un **signal, pas une preuve**, et on l'écrit. Une seconde séance avec
  une autre personne renforcerait le résultat.
- **La confidentialité** : aucune donnée personnelle dans le brief ; la personne le sait.

### 6. Comment on prouve qu'elle marche (écrit avant)

- **Les mesures** :
  - les erreurs glissées **couvertes** par une question (sur 3) ;
  - les erreurs **attrapées par les questions** (sur les couvertes) ;
  - les erreurs **attrapées par le miroir seul** (sur 3) ;
  - les fausses alarmes (différences qui ne sont pas des erreurs) ;
  - les minutes ajoutées par les questions ;
  - les vraies erreurs de lecture trouvées en plus.
- **Les sabotages** : les trois erreurs glissées. **Les témoins** : les quatre questions sur des droits cités. Leurs
  réponses doivent correspondre au calcul, sauf vraie erreur de lecture.
- **Le seuil (proposé, à fixer par Arthur avant la séance)** : **oui**, les exemples entrent dans le miroir, si les
  trois conditions sont réunies :
  - les questions attrapent **au moins une erreur couverte que le miroir a laissée passer** ;
  - elles ajoutent **15 minutes au plus** ;
  - elles produisent **3 fausses alarmes au plus** sur 12.
- **Sinon, non.** Le miroir reste tel quel, et on cherche autre chose pour l'inconnue n° 7.
- **Ce qui ne sera pas prouvé**, même si c'est oui :
  - qu'une autre personne, ou un autre brief, donnerait le même résultat ;
  - que douze questions suffisent pour une grande app ;
  - les erreurs sur les fiches ou les champs : l'essai vise les **droits** seulement.

### 7. Le périmètre

**Touché** : rien dans l'usine. Un dossier d'essai hors du dépôt, et une lecture de brief.

**Pas touché** : le miroir, la description, la matrice, les juges.

**La taille** : une demi-journée de préparation (Claude Code), une séance de 45 minutes (la personne, Arthur), une heure
de bilan.

**Le coût IA** : une lecture de brief, soit les sept lecteurs, par la session isolée.

**Le risque** : faible pour l'usine ; le vrai risque est de surinterpréter un essai à une seule personne.

### 8. Questions pour le vérificateur (Codex)

1. Choisir les huit questions d'après l'**origine** des droits, deviné ou cité, sans regarder leur valeur : est-ce un
   biais ?
2. Trois erreurs tirées au hasard **après** les questions : est-ce le bon compromis entre réalisme et mesure ?
3. Le brief écrit par la personne elle-même, ou un brief fixe : lequel ?
4. L'ordre « à l'aveugle, puis le miroir » avantage le miroir : faut-il deux personnes, l'une avec le miroir seul ?
5. Les seuils proposés au §6 sont-ils raisonnables ?

## Vérification

…

## Après : le compte rendu

…

## Petit lexique

- **À l'aveugle** : sans voir ce que l'usine a calculé.
- **Droit deviné** : un droit que l'usine a posé par une règle par défaut, parce que le brief ne disait rien.
- **Droit cité** : un droit justifié par une phrase du brief.
- **Erreur glissée** : une erreur mise exprès dans la description, pour voir si la méthode l'attrape (un sabotage).
- **Couverte** : une erreur glissée sur laquelle une des douze questions porte.
