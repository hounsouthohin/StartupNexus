# Mutants — notes-frais

44 mutants · 0 invalides (le schéma ne compile plus) · 44 valides
**Tués : 40/44 (90.9 %)** · survivants : 4 · plantages : 0

## Survivants et plantages (à examiner)

- **survivant** l.37 — élargir : « auth().role == 'employee' » remplacé par « auth() != null »
  `@@allow('read', auth() != null && ownerId == auth().id)`
  128/128 conformes à la matrice
- **survivant** l.37 — oublier une condition : condition « auth().role == 'employee' » retirée
  `@@allow('read', ownerId == auth().id)`
  128/128 conformes à la matrice
- **survivant** l.42 — élargir : « auth().role == 'employee' » remplacé par « auth() != null »
  `@@allow('update', auth() != null && ownerId == auth().id)`
  128/128 conformes à la matrice
- **survivant** l.42 — oublier une condition : condition « auth().role == 'employee' » retirée
  `@@allow('update', ownerId == auth().id)`
  128/128 conformes à la matrice

## Tous les mutants

- tué · l.37 · supprimer · règle supprimée — • employee / ExpenseReport / voir : les siennes seulement (0, attendu 2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- survivant · l.37 · élargir · « auth().role == 'employee' » remplacé par « auth() != null » — 128/128 conformes à la matrice
- survivant · l.37 · oublier une condition · condition « auth().role == 'employee' » retirée — 128/128 conformes à la matrice
- tué · l.37 · oublier une condition · condition « ownerId == auth().id » retirée — • employee / ExpenseReport / voir : les siennes seulement (4, attendu 2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.38 · supprimer · règle supprimée — • manager / ExpenseReport / voir : toutes (0/4) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.38 · élargir · « auth().role == 'manager' » remplacé par « auth() != null » — • intrus / ExpenseReport / voir : rien (4) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.40 · supprimer · règle supprimée — • employee / ExpenseReport / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.40 · élargir · « auth().role == 'employee' » remplacé par « auth() != null » — • intrus / ExpenseReport / créer : à son propre nom : attendu REFUSÉ, obtenu PERMIS
- tué · l.40 · oublier une condition · condition « auth().role == 'employee' » retirée — • intrus / ExpenseReport / créer : à son propre nom : attendu REFUSÉ, obtenu PERMIS
- tué · l.40 · oublier une condition · condition « ownerId == auth().id » retirée — • employee / ExpenseReport / créer : au nom d'un autre employee : attendu REFUSÉ, obtenu PERMIS
- tué · l.40 · oublier une condition · condition « status == draft » retirée — • employee / ExpenseReport / créer : directement « submitted » : attendu REFUSÉ, obtenu PERMIS
- tué · l.42 · supprimer · règle supprimée — • employee / ExpenseReport / modifier en « draft » : attendu PERMIS, obtenu REFUSÉ (not-found)
- survivant · l.42 · élargir · « auth().role == 'employee' » remplacé par « auth() != null » — 128/128 conformes à la matrice
- survivant · l.42 · oublier une condition · condition « auth().role == 'employee' » retirée — 128/128 conformes à la matrice
- tué · l.42 · oublier une condition · condition « ownerId == auth().id » retirée — • employee / ExpenseReport / modifier : la fiche d'un autre : attendu REFUSÉ, obtenu PERMIS
- tué · l.43 · supprimer · règle supprimée — • manager / ExpenseReport / état « submitted » → « approved » : attendu PERMIS, obtenu REFUSÉ (not-found)
- tué · l.43 · élargir · « auth().role == 'manager' » remplacé par « auth() != null » — • employee / ExpenseReport / modifier : la fiche d'un autre : attendu REFUSÉ, obtenu PERMIS
- tué · l.46 · supprimer · règle supprimée — • employee / ExpenseReport / modifier en « draft » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.46 · élargir · « auth().role == 'employee' » remplacé par « auth() != null » — • manager / ExpenseReport / modifier en « draft » : attendu REFUSÉ, obtenu PERMIS
- tué · l.46 · oublier une condition · condition « auth().role == 'employee' » retirée — • manager / ExpenseReport / modifier en « draft » : attendu REFUSÉ, obtenu PERMIS
- tué · l.46 · oublier une condition · condition « before().status == draft » retirée — • employee / ExpenseReport / état « submitted » → « draft » : attendu REFUSÉ, obtenu PERMIS
- tué · l.46 · oublier une condition · condition « status == draft » retirée — • employee / ExpenseReport / état « draft » → « approved » : attendu REFUSÉ, obtenu PERMIS
- tué · l.48 · supprimer · règle supprimée — • employee / ExpenseReport / état « draft » → « submitted » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.48 · élargir · « auth().role == 'employee' » remplacé par « auth() != null » — • manager / ExpenseReport / état « draft » → « submitted » : attendu REFUSÉ, obtenu PERMIS
- tué · l.48 · oublier une condition · condition « auth().role == 'employee' » retirée — • manager / ExpenseReport / état « draft » → « submitted » : attendu REFUSÉ, obtenu PERMIS
- tué · l.48 · oublier une condition · condition « before().status == draft » retirée — • employee / ExpenseReport / état « approved » → « submitted » : attendu REFUSÉ, obtenu PERMIS
- tué · l.48 · oublier une condition · condition « status == submitted » retirée — • employee / ExpenseReport / état « draft » → « approved » : attendu REFUSÉ, obtenu PERMIS
- tué · l.48 · oublier une condition · condition « label == before().label » retirée — • employee / ExpenseReport / étape « draft » → « submitted » en changeant aussi label : attendu REFUSÉ, obtenu PERMIS
- tué · l.48 · oublier une condition · condition « amount == before().amount » retirée — • employee / ExpenseReport / étape « draft » → « submitted » en changeant aussi amount : attendu REFUSÉ, obtenu PERMIS
- tué · l.49 · supprimer · règle supprimée — • manager / ExpenseReport / état « submitted » → « approved » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.49 · élargir · « auth().role == 'manager' » remplacé par « auth() != null » — • employee / ExpenseReport / état « submitted » → « approved » : attendu REFUSÉ, obtenu PERMIS
- tué · l.49 · oublier une condition · condition « auth().role == 'manager' » retirée — • employee / ExpenseReport / état « submitted » → « approved » : attendu REFUSÉ, obtenu PERMIS
- tué · l.49 · oublier une condition · condition « before().status == submitted » retirée — • manager / ExpenseReport / état « draft » → « approved » : attendu REFUSÉ, obtenu PERMIS
- tué · l.49 · oublier une condition · condition « (status == approved || status == refused) » retirée — • manager / ExpenseReport / état « submitted » → « draft » : attendu REFUSÉ, obtenu PERMIS
- tué · l.49 · oublier une condition · condition « label == before().label » retirée — • manager / ExpenseReport / étape « submitted » → « approved » en changeant aussi label : attendu REFUSÉ, obtenu PERMIS
- tué · l.49 · oublier une condition · condition « amount == before().amount » retirée — • manager / ExpenseReport / étape « submitted » → « approved » en changeant aussi amount : attendu REFUSÉ, obtenu PERMIS
- tué · l.50 · supprimer · règle supprimée — • manager / ExpenseReport / état « approved » → « reimbursed » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.50 · élargir · « auth().role == 'manager' » remplacé par « auth() != null » — • employee / ExpenseReport / état « approved » → « reimbursed » : attendu REFUSÉ, obtenu PERMIS
- tué · l.50 · oublier une condition · condition « auth().role == 'manager' » retirée — • employee / ExpenseReport / état « approved » → « reimbursed » : attendu REFUSÉ, obtenu PERMIS
- tué · l.50 · oublier une condition · condition « before().status == approved » retirée — • manager / ExpenseReport / état « draft » → « reimbursed » : attendu REFUSÉ, obtenu PERMIS
- tué · l.50 · oublier une condition · condition « status == reimbursed » retirée — • manager / ExpenseReport / état « approved » → « draft » : attendu REFUSÉ, obtenu PERMIS
- tué · l.50 · oublier une condition · condition « label == before().label » retirée — • manager / ExpenseReport / étape « approved » → « reimbursed » en changeant aussi label : attendu REFUSÉ, obtenu PERMIS
- tué · l.50 · oublier une condition · condition « amount == before().amount » retirée — • manager / ExpenseReport / étape « approved » → « reimbursed » en changeant aussi amount : attendu REFUSÉ, obtenu PERMIS
- tué · l.52 · supprimer · règle supprimée — • employee / ExpenseReport / modifier : changer le propriétaire : attendu REFUSÉ, obtenu PERMIS