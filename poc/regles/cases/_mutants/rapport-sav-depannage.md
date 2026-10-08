# Mutants — sav-depannage

50 mutants · 0 invalides (le schéma ne compile plus) · 50 valides
**Tués : 36/50 (72 %)** · survivants : 14 · plantages : 0

## Survivants et plantages (à examiner)

- **survivant** l.74 — élargir : « auth().role == 'staff' » remplacé par « auth() != null »
  `@@allow('post-update', auth() != null && ((before().status == open && status == open) || (before().status == in_progress && status == in_progress) || (before().status == closed && status == closed) || (before().status == paid && status == paid)))`
  124/124 conformes à la matrice
- **survivant** l.74 — oublier une condition : condition « auth().role == 'staff' » retirée
  `@@allow('post-update', ((before().status == open && status == open) || (before().status == in_progress && status == in_progress) || (before().status == closed && status == closed) || (before().status == paid && status == paid)))`
  124/124 conformes à la matrice
- **survivant** l.76 — élargir : « auth().role == 'staff' » remplacé par « auth() != null »
  `@@allow('post-update', auth() != null && before().status == open && status == in_progress && summary == before().summary)`
  124/124 conformes à la matrice
- **survivant** l.76 — oublier une condition : condition « auth().role == 'staff' » retirée
  `@@allow('post-update', before().status == open && status == in_progress && summary == before().summary)`
  124/124 conformes à la matrice
- **survivant** l.77 — élargir : « auth().role == 'staff' » remplacé par « auth() != null »
  `@@allow('post-update', auth() != null && before().status == in_progress && status == closed && summary == before().summary)`
  124/124 conformes à la matrice
- **survivant** l.77 — oublier une condition : condition « auth().role == 'staff' » retirée
  `@@allow('post-update', before().status == in_progress && status == closed && summary == before().summary)`
  124/124 conformes à la matrice
- **survivant** l.78 — élargir : « auth().role == 'staff' » remplacé par « auth() != null »
  `@@allow('post-update', auth() != null && before().status == closed && status == paid && summary == before().summary)`
  124/124 conformes à la matrice
- **survivant** l.78 — oublier une condition : condition « auth().role == 'staff' » retirée
  `@@allow('post-update', before().status == closed && status == paid && summary == before().summary)`
  124/124 conformes à la matrice
- **survivant** l.98 — élargir : « auth().role == 'staff' » remplacé par « auth() != null »
  `@@allow('post-update', auth() != null && ((before().status == todo && status == todo) || (before().status == done && status == done)))`
  124/124 conformes à la matrice
- **survivant** l.98 — oublier une condition : condition « auth().role == 'staff' » retirée
  `@@allow('post-update', ((before().status == todo && status == todo) || (before().status == done && status == done)))`
  124/124 conformes à la matrice
- **survivant** l.99 — élargir : « auth().role == 'staff' » remplacé par « auth() != null »
  `@@allow('post-update', auth() != null && before().status == todo && status == done && label == before().label)`
  124/124 conformes à la matrice
- **survivant** l.99 — oublier une condition : condition « auth().role == 'staff' » retirée
  `@@allow('post-update', before().status == todo && status == done && label == before().label)`
  124/124 conformes à la matrice
- **survivant** l.99 — oublier une condition : condition « before().status == todo » retirée
  `@@allow('post-update', auth().role == 'staff' && status == done && label == before().label)`
  124/124 conformes à la matrice
- **survivant** l.99 — oublier une condition : condition « status == done » retirée
  `@@allow('post-update', auth().role == 'staff' && before().status == todo && label == before().label)`
  124/124 conformes à la matrice

## Tous les mutants

- tué · l.28 · supprimer · règle supprimée — • staff / Customer / voir : toutes (0/1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.28 · élargir · « auth().role == 'staff' » remplacé par « auth() != null » — • intrus / Customer / voir : rien (1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.37 · supprimer · règle supprimée — • staff / SocketType / voir : toutes (0/4) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.37 · élargir · « auth().role == 'staff' » remplacé par « auth() != null » — • intrus / SocketType / voir : rien (4) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.50 · supprimer · règle supprimée — • staff / Machine / voir : toutes (0/2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.51 · supprimer · règle supprimée — • staff / Machine / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.70 · supprimer · règle supprimée — • staff / Intervention / voir : toutes (0/2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.71 · supprimer · règle supprimée — • staff / Intervention / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.71 · oublier une condition · condition « check(machine, 'update') » retirée — • visitor / Intervention / créer : attendu REFUSÉ, obtenu PERMIS
- tué · l.71 · oublier une condition · condition « status == open » retirée — • staff / Intervention / créer : directement « in_progress » : attendu REFUSÉ, obtenu PERMIS
- tué · l.72 · supprimer · règle supprimée — • staff / Intervention / modifier en « open » : attendu PERMIS, obtenu REFUSÉ (not-found)
- tué · l.74 · supprimer · règle supprimée — • staff / Intervention / modifier en « open » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.74 · élargir · « auth().role == 'staff' » remplacé par « auth() != null » — 124/124 conformes à la matrice
- survivant · l.74 · oublier une condition · condition « auth().role == 'staff' » retirée — 124/124 conformes à la matrice
- tué · l.74 · oublier une condition · condition « ((before().status == open && status == open) || (before().status == in_progress && status == in_progress) || (before().status == closed && status == closed) || (before().status == paid && status == paid)) » retirée — • staff / Intervention / état « open » → « closed » : attendu REFUSÉ, obtenu PERMIS
- tué · l.76 · supprimer · règle supprimée — • staff / Intervention / état « open » → « in_progress » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.76 · élargir · « auth().role == 'staff' » remplacé par « auth() != null » — 124/124 conformes à la matrice
- survivant · l.76 · oublier une condition · condition « auth().role == 'staff' » retirée — 124/124 conformes à la matrice
- tué · l.76 · oublier une condition · condition « before().status == open » retirée — • staff / Intervention / état « closed » → « in_progress » : attendu REFUSÉ, obtenu PERMIS
- tué · l.76 · oublier une condition · condition « status == in_progress » retirée — • staff / Intervention / état « open » → « closed » : attendu REFUSÉ, obtenu PERMIS
- tué · l.76 · oublier une condition · condition « summary == before().summary » retirée — • staff / Intervention / étape « open » → « in_progress » en changeant aussi summary : attendu REFUSÉ, obtenu PERMIS
- tué · l.77 · supprimer · règle supprimée — • staff / Intervention / état « in_progress » → « closed » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.77 · élargir · « auth().role == 'staff' » remplacé par « auth() != null » — 124/124 conformes à la matrice
- survivant · l.77 · oublier une condition · condition « auth().role == 'staff' » retirée — 124/124 conformes à la matrice
- tué · l.77 · oublier une condition · condition « before().status == in_progress » retirée — • staff / Intervention / état « open » → « closed » : attendu REFUSÉ, obtenu PERMIS
- tué · l.77 · oublier une condition · condition « status == closed » retirée — • staff / Intervention / état « in_progress » → « open » : attendu REFUSÉ, obtenu PERMIS
- tué · l.77 · oublier une condition · condition « summary == before().summary » retirée — • staff / Intervention / étape « in_progress » → « closed » en changeant aussi summary : attendu REFUSÉ, obtenu PERMIS
- tué · l.78 · supprimer · règle supprimée — • staff / Intervention / état « closed » → « paid » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.78 · élargir · « auth().role == 'staff' » remplacé par « auth() != null » — 124/124 conformes à la matrice
- survivant · l.78 · oublier une condition · condition « auth().role == 'staff' » retirée — 124/124 conformes à la matrice
- tué · l.78 · oublier une condition · condition « before().status == closed » retirée — • staff / Intervention / état « open » → « paid » : attendu REFUSÉ, obtenu PERMIS
- tué · l.78 · oublier une condition · condition « status == paid » retirée — • staff / Intervention / état « closed » → « open » : attendu REFUSÉ, obtenu PERMIS
- tué · l.78 · oublier une condition · condition « summary == before().summary » retirée — • staff / Intervention / étape « closed » → « paid » en changeant aussi summary : attendu REFUSÉ, obtenu PERMIS
- tué · l.79 · supprimer · règle supprimée — • staff / Intervention / étape « open » → « in_progress » en changeant aussi machineId : attendu REFUSÉ, obtenu PERMIS
- tué · l.95 · supprimer · règle supprimée — • staff / Action / voir : toutes (0/1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.96 · supprimer · règle supprimée — • staff / Action / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.96 · oublier une condition · condition « check(intervention, 'update') » retirée — • visitor / Action / créer : attendu REFUSÉ, obtenu PERMIS
- tué · l.96 · oublier une condition · condition « status == todo » retirée — • staff / Action / créer : directement « done » : attendu REFUSÉ, obtenu PERMIS
- tué · l.97 · supprimer · règle supprimée — • staff / Action / modifier en « todo » : attendu PERMIS, obtenu REFUSÉ (not-found)
- tué · l.98 · supprimer · règle supprimée — • staff / Action / modifier en « todo » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.98 · élargir · « auth().role == 'staff' » remplacé par « auth() != null » — 124/124 conformes à la matrice
- survivant · l.98 · oublier une condition · condition « auth().role == 'staff' » retirée — 124/124 conformes à la matrice
- tué · l.98 · oublier une condition · condition « ((before().status == todo && status == todo) || (before().status == done && status == done)) » retirée — • staff / Action / état « done » → « todo » : attendu REFUSÉ, obtenu PERMIS
- tué · l.99 · supprimer · règle supprimée — • staff / Action / état « todo » → « done » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.99 · élargir · « auth().role == 'staff' » remplacé par « auth() != null » — 124/124 conformes à la matrice
- survivant · l.99 · oublier une condition · condition « auth().role == 'staff' » retirée — 124/124 conformes à la matrice
- survivant · l.99 · oublier une condition · condition « before().status == todo » retirée — 124/124 conformes à la matrice
- survivant · l.99 · oublier une condition · condition « status == done » retirée — 124/124 conformes à la matrice
- tué · l.99 · oublier une condition · condition « label == before().label » retirée — • staff / Action / étape « todo » → « done » en changeant aussi label : attendu REFUSÉ, obtenu PERMIS
- tué · l.100 · supprimer · règle supprimée — • staff / Action / étape « todo » → « done » en changeant aussi interventionId : attendu REFUSÉ, obtenu PERMIS