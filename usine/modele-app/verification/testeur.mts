// ▌ VERSION 1.1 — 7 oct 2026 (N1.0b). LES VÉRIFICATIONS SONT CELLES DE LA v1.0, figée et prouvée par
// ▌ mutation (etudes/04-testeur-prouve.md ; source : poc/regles/run.ts). Changements, et leur nature :
// ▌  1. adaptation d'entrée : la matrice attendue et la description sont lues dans verification/
// ▌     (fichiers produits par l'usine) au lieu du banc de matrices ;
// ▌  2. adaptation d'entrée : l'adaptateur (données de test) est construit par verification/cas.ts
// ▌     depuis la description, au lieu d'être écrit à la main ;
// ▌  3. besoin nouveau : une fiche sans champ texte n'a pas de vérification « modifier » (editField).
// ▌ VERSION 1.2 — 8 oct 2026 (N1.1). Changements, et leur nature :
// ▌  4. trou de couverture : « une étape ne change que l'état » n'essayait de changer que les champs
// ▌     texte, nombre et oui/non ; les dates, montants et choix étaient sautés en silence ;
// ▌  5. trou de couverture : les champs facultatifs n'étaient jamais vides dans les données ; chaque
// ▌     étape permise est maintenant essayée champs facultatifs VIDES puis REMPLIS, et l'étape qui
// ▌     les remplit, les vide ou les change est refusée (défaut réel trouvé : NULL == NULL en SQL) ;
// ▌  6. trou de couverture (trouvé par mutation) : qui peut MODIFIER une fiche ne peut pas changer sa
// ▌     date de création (l'antidater) — essayé seulement pendant une étape jusque-là.
// ▌ Re-prouvée par mutation (usine/preuve_regles.mts) avant d'être crue.
// ▌ VERSION 1.3 — 8 oct 2026 (N1.1b, architecture en blocs). Changement, et sa nature :
// ▌  7. structure seulement : le fichier unique est découpé en un NOYAU (noyau.mts) et un module par
// ▌     bloc (blocs/*.mts) — AUCUNE vérification ajoutée, retirée ou modifiée : la liste complète des
// ▌     vérifications et leurs verdicts sont identiques à ceux de la v1.2 sur 3 apps (comparaison
// ▌     TESTEUR_DETAIL), et les preuves par mutation redonnent les mêmes scores.
// ▌ VERSION 1.4 — 9 oct 2026 (N1.2, formulaires). Changement, et sa nature :
// ▌  8. besoin nouveau (les formulaires rendent les liens modifiables) : en MODIFIANT, pointer une fiche
// ▌     qu'on ne voit pas, ou d'un autre propriétaire, est refusé ; re-désigner une fiche visible du
// ▌     même propriétaire reste permis (blocs/modifier.mts) ;
// ▌  9. trou de couverture (trouvé par l'app d'essai des types) : la suppression permise seulement
// ▌     dans certains états est essayée état par état (blocs/supprimer.mts) ;
// ▌ 10. besoin nouveau (doctrine d'intégrité) : même qui peut supprimer ne supprime pas une fiche que
// ▌     d'autres désignent ; qui ne voit une fiche qu'au travers d'autres ne re-désigne pas ce lien.
// ▌ VERSION 1.5 — 10 oct 2026 (N1.3, fiches enfants). Changement, et sa nature :
// ▌ 11. besoin nouveau (bloc « enfant », doctrine du 10 oct) : les LIGNES d'une fiche ont leur bloc
// ▌     (blocs/enfant.mts) — voir celles des parents qu'on voit ; gérer selon l'état du parent ; jamais
// ▌     déplacée ; cascade. Les autres blocs ne jugent plus les lignes (noyau : `enfants`), et l'intégrité
// ▌     ne compte pas les lignes d'une fiche parmi ce qui la retient (blocs/supprimer.mts). Pour une app
// ▌     SANS fiche enfant, les vérifications sont inchangées.
// ▌ Toute modification ultérieure = nouvelle version, notée avec sa nature (erreur / besoin / rustine).
// Testeur générique : lit la matrice de l'app et essaie chaque case contre la base, avec le client AVEC
// règles, rôle par rôle. Livré avec l'app : il resservira à chaque évolution.
// Usage (dans l'app) : npx tsx --env-file=.env.local verification/testeur.mts
import { lancer } from './noyau.mts';
import { circuit } from './blocs/circuit.mts';
import { creer } from './blocs/creer.mts';
import { enfant } from './blocs/enfant.mts';
import { modifier } from './blocs/modifier.mts';
import { supprimer } from './blocs/supprimer.mts';
import { voir } from './blocs/voir.mts';

// L'ordre compte (mêmes données, mêmes cibles) : « voir » pour tous d'abord, puis les actions.
// (N1.3) les lignes (fiches enfants) sont jugées par leur propre bloc, « enfant ».
await lancer([voir], [creer, modifier, circuit, supprimer, enfant]);
