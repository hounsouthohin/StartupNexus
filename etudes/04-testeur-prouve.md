# Étude 04 — E4 : prouver le testeur

*7 octobre 2026. Suite de l'étude 03. Projet jetable : `poc/regles/`. Ni l'usine ni les schémas
d'origine n'ont été modifiés.*

## 1. La question

Le testeur `run.ts` (étude 03) disait « 479/479 ». Mais un testeur peut se tromper : s'il laisse
passer des erreurs, ses chiffres rassurent à tort. Avant de s'y fier, il fallait le prouver.

## 2. La méthode : le test par mutation

Un programme (`poc/regles/mutate.ts`) prend chaque schéma et y introduit **une erreur à la fois** —
supprimer une règle, ouvrir une action à « tout connecté », oublier une des conditions d'une règle —
puis relance le testeur. Une erreur signalée = mutant **tué**. Une erreur non signalée = mutant
**survivant**, examiné un par un : soit un trou du testeur, soit une erreur **sans effet** sur le
comportement (on dit « équivalente »).

## 3. Résultats (testeur final, version figée 1.0)

| Cas | Erreurs introduites | Attrapées | Sans effet | Bénignes non testées | À vérifier |
|---|---|---|---|---|---|
| notes de frais | 44 | 40 | 4 | 0 | 0 |
| garage | 46 | 35 | 9 | 2 | 0 |
| atelier (sans intrus*) | 50 | 40 | 8 | 2 | 0 |
| agence (sans intrus*) | 70 | 54 | 11 | 2 | 3 |
| SAV | 50 | 36 | 14 | 0 | 0 |
| **Total** | **260** | **205** | **46** | **6** | **3** |

**Erreurs qui changent le comportement : 205 attrapées sur 214, soit 95,8 %** (critère : 95 %). ✔
\* voir §5 : ces deux schémas d'origine échouent face à l'intrus, il a fallu l'écarter pour les mesurer.

- **Sans effet (46)** : la condition de rôle est écrite deux fois (dans « qui peut toucher » et dans
  « résultat permis ») ; ou elle double une condition de propriété (seul un employé possède des
  notes) ; ou le circuit n'a que 2 états ; ou le parent est toujours public. Retirer l'une ne change rien.
- **Bénignes non testées (6)** : sans la condition de rôle, une personne qui a CHANGÉ de rôle (client
  devenu patron) peut encore modifier son ancien profil. Sans gravité ; non testé.
- **À vérifier (3)** : élargir la lecture des réservations de l'agence à « tout connecté ». L'intrus
  (§4) attrape ce genre d'erreur — vérifié sur le SAV — mais il a dû être écarté de l'agence (§5).

Le classement « sans effet » est un jugement de ma part, mutant par mutant ; les listes complètes
sont dans `poc/regles/cases/_mutants/rapport-<cas>.md`.

## 4. Ce que l'E4 a corrigé dans le testeur (premier passage : 65,9 % seulement)

| # | Correction | Nature |
|---|---|---|
| 1 | Chaque écriture est jugée en **relisant la base**, plus sur la réponse | défaut de conception (le plus grave — §5) |
| 2 | Qui n'a pas le droit de créer essaie aussi **à son propre nom** | trou de couverture |
| 3 | Une étape du circuit est essayée en changeant **chacun des autres champs**, sur **chaque flèche** | trou de couverture |
| 4 | **Changement de rôle** : un employé promu garde ses anciennes fiches | trou de couverture (cas réel) |
| 5 | **L'intrus** : connecté, mais sans rôle déclaré → droits du visiteur | trou de couverture (cas réel) |
| 6 | « Créer au nom d'un autre » ne change plus que le propriétaire | **erreur de mon test** (masquait une règle) |
| 7 | Le changement de rôle recrée l'ancien profil quand le lien l'exige | **erreur de mon test** (plantage) |
| — | Données de test : au moins **2 fiches de chaque sorte** | données trop pauvres (atelier, SAV, agence) |

Le testeur est **figé en version 1.0** (empreinte `872112f0c6d8`, 450 lignes). Toute modification
future sera une nouvelle version, notée avec sa nature.

## 5. Trois découvertes pour l'usine

1. **ZenStack 3.9.7 peut répondre « refusé » alors que l'écriture a eu lieu.** Quand l'auteur n'a plus
   le droit de relire le résultat (il a changé le propriétaire, créé au nom d'un autre), ZenStack
   renvoie « résultat non relisible »… mais la base est déjà modifiée (vérifié par une sonde,
   `poc/regles/probe-readback.ts`). Nos règles d'origine bloquent ces écritures en amont, donc les
   apps de l'essai sont saines. Mais **le traducteur ne doit jamais compter sur la relecture** : chaque
   interdiction doit être écrite comme une règle. À signaler à ZenStack.
2. **« Visible de tous les connectés » doit lister les rôles, jamais « connecté ».** Dans l'atelier et
   l'agence, j'avais traduit ce préréglage par `auth() != null`. Avec l'intrus, les catalogues internes
   (tarifs, destinations, domaines, créneaux) sont lisibles par **n'importe qui se créant un compte**
   si l'inscription reste ouverte. Correction mécanique du patron n°3 (étude 03) : `auth().role` parmi
   les rôles déclarés. Schémas d'origine non corrigés (hors fiche) — d'où l'intrus écarté pour mesurer.
3. **Le futur générateur de données de test** devra créer au moins 2 fiches de chaque sorte, des
   fiches pour au moins 2 propriétaires par rôle, et savoir simuler un changement de rôle.

## 6. Limites

- Les 3 sortes d'erreurs introduites ne couvrent pas tout (par exemple : inverser une comparaison,
  confondre deux états). Elles couvrent les oublis les plus probables d'un traducteur.
- Le classement « sans effet » est manuel (46 mutants, listés).
- L'intrus n'a pas pu être mesuré sur l'atelier et l'agence tant que leurs schémas ne sont pas corrigés.

## Concepts

- **Test par mutation** : on abîme exprès le code testé pour vérifier que les tests le remarquent.
  *Pourquoi* : un test qui ne voit rien quand on casse quelque chose ne protège de rien.
- **Mutant équivalent** : une modification qui ne change aucun comportement observable ; aucun test
  ne peut la détecter, ce n'est pas un défaut du testeur.
- **Défense en profondeur** : la même protection à deux endroits ; si l'un est oublié, l'autre tient.
  C'est ce qui rend 46 mutants « sans effet ».

## Rejouer

```
cd poc/regles
npx tsx run.ts <cas>                 # le testeur (avec l'intrus)
npx tsx mutate.ts <cas>              # les mutants ; SANS_INTRUS=1 pour atelier et agence
npx tsx probe-readback.ts            # la sonde « refusé mais écrit »
```
