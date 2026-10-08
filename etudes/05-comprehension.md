# Étude 05 — E5 : l'IA comprend-elle un vrai brief ? (partie 1, sans miroir)

*7 octobre 2026. Projet jetable : `poc/comprehension/`. L'usine n'a pas été modifiée (le calculateur
de la phase 3 est utilisé en lecture seule).*

## 1. La question

C'est le risque n°1 de la nouvelle conception : à partir d'un VRAI brief, des agents IA
produisent-ils une description juste de l'app (qui se connecte, quelles fiches, quels circuits,
quels droits, ce qui est hors stock) ? Critère fixé d'avance : **≥ 7/10 justes → automatiser ;
< 5/10 → configurateur assisté ; entre les deux → examiner les causes.**

## 2. Ce qui a été fait

- **10 vrais briefs** (lot d'apprentissage choisi par l'utilisateur, textes originaux récupérés) :
  7 dans le périmètre, 3 hors périmètre exprès. Quatre des sept font 2 à 3 lignes chez le client
  lui-même.
- **Grille de référence écrite AVANT de lancer l'IA** (`poc/comprehension/references.yaml`) :
  pour chaque brief, les faits explicites (citation + critère précis), les points ouverts (non
  jugés : ce sont des questions pour le miroir), le périmètre, les besoins hors stock attendus, et
  4 règles de prudence. *Adaptation de la fiche* : la fiche prévoyait une comparaison case par case
  de matrices ; sur des briefs de 2 lignes, elle aurait surtout mesuré mes propres choix sur ce que
  le brief ne dit pas. Le verdict et les seuils sont inchangés.
- **Les agents** (`poc/comprehension/comprendre.py`) : **5 questions** au lieu des 4 prévues —
  acteurs, fiches, circuits, **droits explicites** (ajouté : ne rentrait dans aucune des 4, et c'est
  ce qui avait coûté 13 exceptions à l'agence en E2), périmètre et hors stock. Chaque réponse est
  contrôlée par programme (forme stricte, identifiants connus, citations mot pour mot) et renvoyée
  avec l'erreur si elle est refusée (2 essais de plus).
- **3 modèles** : gpt-4o-mini (celui de l'ancienne usine), gpt-5.4-mini (récent, économique),
  gpt-5.5 (le plus fort).

## 3. Résultats

| Brief | gpt-4o-mini | gpt-5.4-mini | gpt-5.5 |
|---|---|---|---|
| cabinet pluridisciplinaire | ✗ jugé hors périmètre | ✗ dossiers absents ; droits « tout interdit » | ✗ **dossiers visibles de tous** (fuite) |
| rénovation | ✗ hors ; échec | ✓ | ✓ |
| autocars | ✗ hors ; échec | ✗ chauffeurs et véhicules absents ; course sans client | ✓ |
| organisme de formation | ✗ hors | ✓ | ✓ |
| gestion immobilière | ✗ hors (mauvaise raison) | ✓ | ✓ |
| union sportive | ✗ hors ; échec | ✗ adhésion et participation non reliées ; « annulation » lue comme suppression | ✗ suppression des fiches membres oubliée |
| mesures sur le terrain | ✗ hors | ✗ hors (confond « hors stock » et « hors périmètre ») | non mesuré |
| marketplace (hors) | ✓ | ✓ | non mesuré |
| réseau social (hors) | ✓ | ✓ | non mesuré |
| app mobile transport (hors) | ✓ | ✓ | non mesuré |
| **Total** | **3/10** | **6/10** | **4/6 mesurés** |

La mesure de gpt-5.5 s'est arrêtée : **les crédits du compte OpenAI sont épuisés.**

**Verdict selon le critère fixé d'avance : zone intermédiaire (6/10)** → examiner les causes.

## 4. Les causes — aucune n'est du hasard

| Cause | Briefs touchés | Nature | Correction possible |
|---|---|---|---|
| **A. Trou de vocabulaire : pas de « registre »** (fiches tenues par l'équipe, visibles des seuls responsables). J'ai demandé de les classer en « catalogue », que le calculateur rend visible à tout connecté | cabinet (gpt-5.5) : **la seule fuite de confidentialité** | vocabulaire de la matrice | ajouter la nature « registre », moindre privilège par défaut — rejoint le trou « fiche d'équipe » de l'E2 |
| **B. L'agent « droits » est le plus faible** : il rate un droit écrit (suppression) ou en invente (« annulation » = suppression ; « pas d'accès total » = tout interdire) | union, cabinet | consigne + contrôle | contrôle croisé : le responsable doit voir quelque chose ; consigne par verbe d'action (créer, modifier, supprimer, annuler, valider…) |
| **C. Des personnes ou objets oubliés comme fiches** (l'agent 1 les nomme, l'agent 2 ne les crée pas) | cabinet, autocars (gpt-5.4-mini) | contrôle croisé manquant | chaque « non-utilisateur » doit devenir une fiche (contrôle par programme) |
| **D. Liens oubliés entre fiches** | union, autocars (gpt-5.4-mini) | capacité du modèle | gpt-5.5 les fait ; le miroir les rendra visibles |
| **E. « Hors stock » confondu avec « hors périmètre »** | mesures (gpt-5.4-mini), 7 briefs (gpt-4o-mini) | consigne | phrase explicite dans la consigne |

Bruit sans conséquence sur le verdict : circuits vides inventés (gpt-5.4-mini), livrables du contrat
listés en « hors stock », catalogues sans gestionnaire (personne ne peut créer de devis) — ce dernier
point est exactement ce que le miroir doit montrer au client.

Ce qui marche bien, avec les deux modèles récents : **le hors stock** (paiement, EBP, hors ligne,
cloisonnement par agence, partage fin, comptabilité… tous trouvés, avec citation), **les règles de
prudence** (aucun personnel en inscription libre, stagiaires et adhérents traités en fiches), et
**le hors périmètre** (3/3).

## 5. Ce que ça veut dire

- **Pas de cul-de-sac.** Les erreurs ont 5 causes identifiées, génériques, et 4 sur 5 se corrigent
  par des contrôles déterministes ou une consigne — pas en « espérant que l'IA fasse mieux ».
- **Le modèle compte.** gpt-4o-mini, celui de l'ancienne usine, est inutilisable pour cette tâche.
  Comprendre un brief ne se fait qu'une fois par app : le meilleur modèle coûte quelques centimes.
- **Le vocabulaire de la matrice doit grandir** : la nature « registre » rejoint les 4 trous de l'E2.
  C'est le point le plus important, car c'est le seul qui a produit une fuite.
- **Le miroir reste indispensable** : briefs de 2 lignes = beaucoup de points ouverts.

## 6. Limites

- Le jugement de chaque fait est le mien, contre une grille écrite avant ; les sorties sont
  conservées (`poc/comprehension/sorties/<modèle>/`) et relisibles avec `python voir.py <modèle> <brief>`.
- 10 briefs, une seule passe par modèle : la variance d'un passage à l'autre n'est pas mesurée.
- gpt-5.5 : 6 briefs sur 10 (crédits épuisés).
- Coût exact non mesuré (à enregistrer la prochaine fois).

## 7. E5 bis — après corrections (même grille, inchangée)

Corrections génériques : nature **registre** dans le calculateur ; contrôles croisés (chaque
non-utilisateur devient une fiche, circuits ≥ 2 états, initiateur d'un registre, droits revus si un
acteur ne voit plus rien) ; consignes « droits » (chaque verbe ; annuler ≠ supprimer ; phrase
générale ≠ interdiction) et « périmètre » (hors stock ≠ hors périmètre).

| Modèle | v1 | v2 passage 1 | v2 passage 2 | Coût réel par brief |
|---|---|---|---|---|
| gpt-5.4-mini | 6/10 | 6/10 | 6/10 (erreurs différentes) | **0,014 $** |
| gpt-5.5 | 4/6 | **9/10** | arrêté (budget) | **0,195 $** |

- **gpt-5.5 + v2 : 9/10**, au-dessus du seuil « automatiser » (7/10) — **sur un seul passage** : la
  stabilité n'est pas mesurée (passage 2 arrêté pour ménager le budget).
- **gpt-5.4-mini plafonne à 6/10 et varie** : ses erreurs changent d'un passage à l'autre (session
  oubliée, adhérents devenus utilisateurs, visiteur doté de tous les droits).
- **Le seul échec de gpt-5.5 : le cabinet médical.** Pour rendre l'app utilisable, il nomme les
  professionnels « responsables » des dossiers, donc ils les voient tous. Le partage dossier par
  dossier n'existe pas dans notre vocabulaire : l'IA a choisi l'utilité contre la confidentialité.
  Pistes : consigne de prudence (« si le brief limite l'accès, ne l'élargis pas : signale-le hors
  stock ») et question du miroir sur les registres (« X verra tous les dossiers — d'accord ? »).
- Nouveaux défauts repérés (hors grille) : droits donnés au **visiteur** sur des fiches non publiques
  (gpt-5.4-mini, rénovation) → contrôle croisé à ajouter : un droit « visiteur » seulement sur une
  fiche que l'agent des fiches a déclarée publique ; un responsable qui ne voit rien (gpt-5.5,
  rénovation) → le miroir l'affiche.
- **Coût total de l'E5 bis : 2,30 $ US.**

## 8. E5 fin — les deux derniers défauts graves (version 3)

Corrections génériques : consigne de prudence (un accès que le brief LIMITE n'est pas élargi : le
partage fin est signalé hors stock) ; contrôle croisé (un droit du visiteur seulement sur une fiche
déclarée publique) ; nouvelle question du miroir dans le calculateur (« X verra tous les dossiers,
pas seulement ceux qui le concernent — d'accord ? ») quand un registre est vu en entier par un autre
que le responsable. Banc des matrices : 14/14.

| Brief | gpt-5.5 v2 | gpt-5.5 v3 |
|---|---|---|
| cabinet (confidentialité) | ✗ professionnels « responsables » des dossiers | ✓ dossiers au seul administrateur ; partage fin hors stock |
| rénovation (visiteur) | ✓ | ✓ |
| transport (périmètre) | ✓ (« dans », toléré) | ✓ « hors » |

- Les 7 autres briefs étaient justes en v2 et **n'ont pas été relancés en v3** (budget) : on ne
  peut pas écrire « 10/10 », seulement que les 3 cas fragiles sont corrigés.
- gpt-5.4-mini en v3 : toujours instable (2/5) ; le filet a fonctionné — quand il a donné tous les
  dossiers au professionnel, le miroir a posé la question au client.
- À retenir pour le niveau 1 : en rénovation, l'IA confie les chantiers au seul chef de projet et
  le patron (responsable de l'app) ne voit rien. Le miroir le montre ; faut-il que le responsable
  voie par défaut tous les registres ? Question de doctrine à trancher.
- Coût de l'E5 fin : **0,66 $** (mini 0,08 $ + gpt-5.5 0,58 $). Total E5 bis + fin : 2,96 $.

## Concepts

- **Grille pré-enregistrée** : on écrit ce qu'on attend AVANT de voir les résultats. *Pourquoi* :
  impossible d'ajuster le critère pour que le résultat paraisse bon.
- **Contrôle croisé** : vérifier par programme que deux agents sont d'accord (ce que l'un nomme,
  l'autre doit le traiter). *Pourquoi* : une erreur d'un agent devient visible sans relire à la main.
- **Variance** : un même modèle peut répondre différemment à deux passages ; une seule mesure par
  brief ne dit pas si le résultat est stable.
