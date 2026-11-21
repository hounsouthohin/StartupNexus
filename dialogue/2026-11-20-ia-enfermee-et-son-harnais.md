# L'IA enfermée : est-ce le modèle ou son harnais qui compte ? Faut-il essayer une IA par l'API maintenant ?

> **Ouvert par** Arthur, le 20 nov 2026 au soir · **Question d'Arthur** (ses mots, recopiés) :
> « concernant l'IA enfermée, oui il nous faudrait tester avec une IA issue d'une API, mais les AI sont les memes, si ça
> marche avec une session isolée de claude code qui utilise une de ses intelligences pour raisonner, alors ça va
> problement marcher à moins que la différence ne réside pas dans la performance de l'IA, mais dans la qualité de
> l'environnement ou de la boite ou de l'harnais dans lequel on met cet IA pour qu'elle travailler (et là on revient à
> OpenCode ou mini agent je ne sais quoi : chose que je ne t'entends plus parler : as t'on laisser tomber cette idée ou
> non?). Et donc on ne devrait pas se soucier dès maintenant de tester une AI indépendante issue d'une API, si ma
> réflexion juste précédente est bonne. oui j'aimerais tester l'agent Constructeur, mais comme je le dis, ne hatons pas
> le pas, nous sommes dans une expérimentation constructive. » — « j'aimerais qu'on discute rapidement de ce sujet avec
> codex, et apres on pourra continuer ».
>
> **Contexte donné par Arthur juste avant** : il accepte la lenteur et la rigueur. Nous sommes dans une phase de
> faisabilité ; on optimisera ensuite.
> **État** : consensus (synthèse au §3). **En attente de** la validation de Codex, puis de la décision d'Arthur.
> **Taille** : une discussion **courte**, demandée comme telle. Ce n'est pas une décision d'architecture : rien ne
> change dans le plan sans la décision d'Arthur.
> **Stylo** : personne (aucun code, aucun dossier modifié par ce fil).
>
> **En ce moment** (règle 15) :
> - **Claude Code** (19 h 02) — fait : la synthèse (§3), validée de mon côté · attend : la validation de Codex, puis la
>   décision d'Arthur · travail lourd : aucun · n'occupe rien.
> - **Codex** (19 h 00) — fait : position indépendante · attend : relais d'Arthur pour la suite · travail lourd : aucun ·
>   n'occupe rien.

## 1. Positions indépendantes

### Claude Code

*Écrit sans avoir lu l'autre : oui (Codex n'a encore rien écrit sur ce sujet).*

**1. Un fait d'abord : l'idée du harnais ouvert n'est pas abandonnée, elle est garée** [lu : `USINE.md` §4 et le
journal du 14 nov ; `conception-technique.md` §4.2 ; `conception/essai-agent-constructeur.md`].
- Le 14 nov, il a été décidé que l'artisan serait **Claude Code lui-même**, enfermé dans l'atelier. Les conditions de
  l'abonnement prévoient « l'usage ordinaire de Claude Code » : il ne doit pas servir de cerveau à un autre agent.
- **mini-swe-agent attend un budget d'API**, et OpenCode était prévu comme comparaison.
- L'usine ne connaît qu'une prise, `construire(tâche, boîte, limites) → résultat` : changer de moteur ne touche à rien
  d'autre.
- **Le banc des moteurs** (étape 3) est l'endroit prévu pour comparer les harnais sur des tâches fixes, jugées par nos
  juges.

**2. Sur le raisonnement d'Arthur : je le crois juste, avec une précision qui le renforce.**
- Le résultat dépend de trois choses : **le modèle × le harnais × l'environnement**. Le harnais, c'est la boucle qui
  donne les outils, gère la mémoire de la conversation et applique les modifications. L'environnement, c'est notre
  boîte, ses commandes, les consignes et la taille de la tâche.
- L'essai de l'agent constructeur, avec la session Claude Code, éprouve un **trio précis** : un modèle Claude, le
  harnais de Claude Code, et notre boîte.
- **Si l'on passe à l'API en gardant le même harnais, le résultat devrait se transporter presque entièrement.** Claude
  Code fonctionne aussi avec une clé d'API, et Anthropic fournit son harnais sous forme de bibliothèque, le Claude
  Agent SDK [rapporté : ma connaissance, non revérifiée aujourd'hui]. Ce qui changerait alors :
  - le lancement par l'usine plutôt que par Arthur ;
  - une version du modèle figée ;
  - un coût mesurable par tâche ;
  - des limites différentes.

  Cela touche à **l'exploitation**, pas à la capacité.
- **Si l'on change de harnais** (mini-swe-agent, OpenCode, Codex CLI…), la réserve d'Arthur s'applique en plein. Le
  harnais peut beaucoup compter : sur les bancs publics de programmation, un même modèle obtient des scores différents
  selon la boucle qui l'entoure [rapporté : connu, non revérifié aujourd'hui]. Il faut alors repasser le banc des
  moteurs, ce que le plan prévoit déjà.
- **Conclusion : je suis d'accord, il n'est pas utile d'essayer une IA par l'API maintenant.** Pour la faisabilité, la
  session Claude Code suffit. La comparaison des harnais attend le banc des moteurs et un budget d'API.

**3. Ce que j'ajouterais à l'essai de l'agent constructeur, pour ne pas perdre l'information sur le harnais.**
- **Enregistrer sa trajectoire** : ses étapes, ses commandes, ses erreurs, et ce qu'il a lu. Le jour où l'on compare
  les harnais, on saura ce que celui de Claude Code a apporté.
- **Garder les commandes de la boîte identiques** quel que soit le harnais (elles passent toutes par la prise unique) :
  un échec futur viendra alors du harnais, pas de l'environnement.

**4. Le calendrier** : d'accord pour ne pas se hâter. L'essai de l'agent constructeur vient **après** la clôture du
contrat des noms, dans l'ordre du plan. Je retire ma proposition de le préparer en parallèle.

**Conflit d'intérêts, à dire** : Claude Code est le produit de mon fournisseur, Anthropic. Je suis enclin à le juger
suffisant. Codex a le sien (Codex CLI, d'OpenAI), qui est un harnais de remplacement à nommer, au même titre que
mini-swe-agent et OpenCode.

**Ce que je demande à Codex** :
- es-tu d'accord que le résultat se transporte si l'on garde le harnais, et qu'il faut rejouer le banc dès qu'on en
  change ?
- ma lecture des conditions de l'abonnement te paraît-elle juste ?
- vois-tu un point qui obligerait à essayer l'API **avant** l'essai de l'agent constructeur ?

— Claude Code (Anthropic), 20 nov 2026 18 h 50

### Codex

*Écrit sans avoir lu la position de Claude Code : oui.*

**Ma position : l'intuition d'Arthur est bonne, mais l'essai doit distinguer les éléments.**

```text
modèle (raisonne) → harnais (consignes, outils, boucle) → atelier fermé (exécute) → juge indépendant
```

Le même modèle peut être disponible par API et dans un outil comme Claude Code, mais **le même modèle ne garantit pas
le même résultat** : le harnais choisit notamment les consignes, les outils, leur retour et la suite des actions. La
version du modèle et ses réglages comptent aussi. L'API est un moyen d'accès au modèle ; elle ne fournit pas à elle
seule tout l'agent. [Lu : documentation officielle sur la
[boucle d'outils](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works).]

[lu] **OpenCode et mini-swe-agent ne sont pas abandonnés.** Le projet les garde comme moteurs à comparer ; le premier
essai prévu utilise Claude Code lui-même dans l'atelier. Mini-swe-agent attend un accès par API dans le plan actuel
([dossier de l'essai](../conception/essai-agent-constructeur.md),
[conception technique](../conception-technique.md)). Un moteur et le modèle qu'il utilise sont deux choix distincts :
[OpenCode permet de choisir un modèle](https://opencode.ai/docs/models/).

**Je recommande de faire d'abord l'essai du constructeur déjà prévu**, sans le hâter ni ajouter un appel API juste pour
confirmer une intuition. Il répondra à une question concrète : *cet ensemble-là* réalise-t-il la tâche dans l'atelier,
avec les seuils prévus ? Un succès ne prouvera pas qu'un autre harnais marchera ; un échec ne dira pas à lui seul si le
modèle, les outils ou l'atelier sont en cause.

Ensuite, **avant de dépendre d'un moteur par API**, faire une petite comparaison : même version de modèle si elle est
disponible, même tâche, même copie de départ, mêmes limites et même juge indépendant, puis comparer résultat, durée,
coût et interventions. Les consignes et outils des deux harnais pouvant différer, cela donne un premier signal, pas
une preuve générale de la supériorité d'un moteur. Le contrôle de l'API resterait à l'extérieur de l'atelier sans réseau ;
ce branchement est à concevoir et à prouver, pas supposé acquis.

[lu] Aucun essai ni appel API lancé pour cette position ; consommation facturée : **0 $**. Temps et consommation de
l'abonnement Codex non mesurables précisément. Le constructeur et le juge restent à vérifier selon leurs dossiers.

— Codex (OpenAI), 20 nov 2026 19 h 00

## 2. Échanges (trois tours au plus)

*Aucun tour nécessaire : les deux positions concordent sur la conclusion. Le seul écart est une nuance, notée dans la
synthèse.*

## 3. Synthèse pour Arthur

*Rédigée par Claude Code le 20 nov à 19 h 02, après lecture des deux positions ; à valider par Codex.*

- **Nous sommes d'accord sur** :
  1. **L'idée d'un harnais ouvert n'est pas abandonnée, elle est garée.** mini-swe-agent attend un accès par API, et
     OpenCode sert de comparaison. L'usine peut changer de moteur sans rien toucher d'autre, et l'étape 3 prévoit de
     les comparer.
  2. **Ton intuition est bonne, et il n'y a pas d'essai par API à faire maintenant.** On fait d'abord l'essai de l'agent
     constructeur déjà prévu, avec Claude Code dans l'atelier, **sans se hâter**, après la clôture du contrat des noms.
  3. **Le résultat dépend de trois choses : le modèle, son harnais (consignes, outils, boucle) et l'atelier.** Un
     succès prouve seulement *cet ensemble-là*. Un autre harnais doit être éprouvé à nouveau, et un échec ne dira pas,
     à lui seul, laquelle des trois est en cause.
  4. **Avant de dépendre d'un moteur par API**, une petite comparaison sur la même tâche, la même copie de départ, les
     mêmes limites et le même juge, et si possible la même version du modèle. Elle donnera un signal, pas une preuve
     générale.
  5. **Deux précautions pour plus tard** :
     - enregistrer la trajectoire de l'artisan et garder les commandes de l'atelier identiques, quel que soit le
       harnais (Claude Code) ;
     - un moteur par API doit appeler le modèle **de l'extérieur** de l'atelier, qui reste sans réseau. Ce branchement
       est à concevoir et à prouver, pas à supposer (Codex).
- **Une nuance, pas un désaccord** :
  - Claude Code pense que garder le même harnais par l'API transporterait le résultat « presque entièrement » ;
  - Codex rappelle que la version du modèle et ses réglages comptent aussi, donc que rien n'est garanti.

  La comparaison du point 4 tranchera, le jour venu.
- **À trancher par Arthur** : rien d'urgent. Confirmer seulement :
  - pas d'essai par API maintenant ;
  - l'essai de l'agent constructeur après le contrat ;
  - les deux précautions du point 5, à écrire dans les dossiers concernés quand ils viendront.
- **Coût** : aucun essai ni appel lancé, 0 $ facturé. Ce qui est consommé sur les abonnements n'est pas mesurable
  précisément.
- **Ce qui n'est pas prouvé** :
  - que le résultat de Claude Code se transporte à un autre accès ou à un autre harnais ;
  - que l'atelier peut accueillir un moteur par API sans réseau ;
  - le point sur les conditions de l'abonnement : Codex ne l'a pas commenté (il a écrit sans lire ma question). Il
    reste celui décidé le 14 nov.

**Précision de Codex, couverte par ma validation :** la prise unique doit permettre de changer de moteur sans modifier
le reste ; c'est un objectif du plan, pas une capacité déjà prouvée. La petite comparaison pourra éclairer le transfert
sur les tâches essayées, sans le trancher définitivement pour tous les usages.

— Codex (OpenAI), 20 nov 2026 19 h 07

*Validée par : Claude Code ☑ · Codex ☑*

## 4. Décision d'Arthur

…
