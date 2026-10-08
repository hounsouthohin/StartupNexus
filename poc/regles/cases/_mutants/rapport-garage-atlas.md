# Mutants — garage-atlas

46 mutants · 0 invalides (le schéma ne compile plus) · 46 valides
**Tués : 35/46 (76.1 %)** · survivants : 11 · plantages : 0

## Survivants et plantages (à examiner)

- **survivant** l.29 — élargir : « auth().role == 'client' » remplacé par « auth() != null »
  `@@allow('read,update', auth() != null && userId == auth().id)`
  128/128 conformes à la matrice
- **survivant** l.29 — oublier une condition : condition « auth().role == 'client' » retirée
  `@@allow('read,update', userId == auth().id)`
  128/128 conformes à la matrice
- **survivant** l.42 — élargir : « auth().role == 'client' » remplacé par « auth() != null »
  `@@allow('read', auth() != null && ownerId == auth().id)`
  128/128 conformes à la matrice
- **survivant** l.42 — oublier une condition : condition « auth().role == 'client' » retirée
  `@@allow('read', ownerId == auth().id)`
  128/128 conformes à la matrice
- **survivant** l.64 — élargir : « auth().role == 'client' » remplacé par « auth() != null »
  `@@allow('read', auth() != null && ownerId == auth().id)`
  128/128 conformes à la matrice
- **survivant** l.64 — oublier une condition : condition « auth().role == 'client' » retirée
  `@@allow('read', ownerId == auth().id)`
  128/128 conformes à la matrice
- **survivant** l.68 — élargir : « auth().role == 'owner' » remplacé par « auth() != null »
  `@@allow('update', auth() != null)`
  128/128 conformes à la matrice
- **survivant** l.69 — élargir : « auth().role == 'owner' » remplacé par « auth() != null »
  `@@allow('post-update', auth() != null && before().status == pending && (status == in_progress || status == refused) && description == before().description && vehicleId == before().vehicleId)`
  128/128 conformes à la matrice
- **survivant** l.69 — oublier une condition : condition « auth().role == 'owner' » retirée
  `@@allow('post-update', before().status == pending && (status == in_progress || status == refused) && description == before().description && vehicleId == before().vehicleId)`
  128/128 conformes à la matrice
- **survivant** l.70 — élargir : « auth().role == 'owner' » remplacé par « auth() != null »
  `@@allow('post-update', auth() != null && before().status == in_progress && status == done && description == before().description && vehicleId == before().vehicleId)`
  128/128 conformes à la matrice
- **survivant** l.70 — oublier une condition : condition « auth().role == 'owner' » retirée
  `@@allow('post-update', before().status == in_progress && status == done && description == before().description && vehicleId == before().vehicleId)`
  128/128 conformes à la matrice

## Tous les mutants

- tué · l.28 · supprimer · règle supprimée — • client / ClientProfile / créer : son propre profil (première connexion) : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.28 · élargir · « auth().role == 'client' » remplacé par « auth() != null » — • intrus / ClientProfile / créer : un profil (pas son rôle) : attendu REFUSÉ, obtenu PERMIS
- tué · l.28 · oublier une condition · condition « auth().role == 'client' » retirée — • intrus / ClientProfile / créer : un profil (pas son rôle) : attendu REFUSÉ, obtenu PERMIS
- tué · l.28 · oublier une condition · condition « userId == auth().id » retirée — • client / ClientProfile / créer : le profil de quelqu'un d'autre : attendu REFUSÉ, obtenu PERMIS
- tué · l.29 · supprimer · règle supprimée — • client / ClientProfile / voir : les siennes seulement (0, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- survivant · l.29 · élargir · « auth().role == 'client' » remplacé par « auth() != null » — 128/128 conformes à la matrice
- survivant · l.29 · oublier une condition · condition « auth().role == 'client' » retirée — 128/128 conformes à la matrice
- tué · l.29 · oublier une condition · condition « userId == auth().id » retirée — • client / ClientProfile / voir : les siennes seulement (2, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.30 · supprimer · règle supprimée — • owner / ClientProfile / voir : toutes (0/2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.30 · élargir · « auth().role == 'owner' » remplacé par « auth() != null » — • intrus / ClientProfile / voir : rien (2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.31 · supprimer · règle supprimée — • client / ClientProfile / modifier : changer le propriétaire : attendu REFUSÉ, obtenu PERMIS
- tué · l.42 · supprimer · règle supprimée — • client / Vehicle / voir : les siennes seulement (0, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- survivant · l.42 · élargir · « auth().role == 'client' » remplacé par « auth() != null » — 128/128 conformes à la matrice
- survivant · l.42 · oublier une condition · condition « auth().role == 'client' » retirée — 128/128 conformes à la matrice
- tué · l.42 · oublier une condition · condition « ownerId == auth().id » retirée — • client / Vehicle / voir : les siennes seulement (2, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.43 · supprimer · règle supprimée — • owner / Vehicle / voir : toutes (0/2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.43 · élargir · « auth().role == 'owner' » remplacé par « auth() != null » — • intrus / Vehicle / voir : rien (2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.44 · supprimer · règle supprimée — • owner / Vehicle / modifier : changer le propriétaire : attendu REFUSÉ, obtenu PERMIS
- tué · l.64 · supprimer · règle supprimée — • client / Repair / voir : les siennes seulement (0, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- survivant · l.64 · élargir · « auth().role == 'client' » remplacé par « auth() != null » — 128/128 conformes à la matrice
- survivant · l.64 · oublier une condition · condition « auth().role == 'client' » retirée — 128/128 conformes à la matrice
- tué · l.64 · oublier une condition · condition « ownerId == auth().id » retirée — • client / Repair / voir : les siennes seulement (2, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.65 · supprimer · règle supprimée — • owner / Repair / voir : toutes (0/2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.65 · élargir · « auth().role == 'owner' » remplacé par « auth() != null » — • intrus / Repair / voir : rien (2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.67 · supprimer · règle supprimée — • owner / Repair / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.67 · élargir · « auth().role == 'owner' » remplacé par « auth() != null » — • intrus / Repair / créer : attendu REFUSÉ, obtenu PERMIS
- tué · l.67 · oublier une condition · condition « auth().role == 'owner' » retirée — • visitor / Repair / créer : attendu REFUSÉ, obtenu PERMIS
- tué · l.67 · oublier une condition · condition « status == pending » retirée — • owner / Repair / créer : directement « in_progress » : attendu REFUSÉ, obtenu PERMIS
- tué · l.67 · oublier une condition · condition « vehicle.ownerId == ownerId » retirée — • owner / Repair / créer : en pointant Vehicle d'un AUTRE propriétaire : attendu REFUSÉ, obtenu PERMIS
- tué · l.68 · supprimer · règle supprimée — • owner / Repair / état « pending » → « in_progress » : attendu PERMIS, obtenu REFUSÉ (not-found)
- survivant · l.68 · élargir · « auth().role == 'owner' » remplacé par « auth() != null » — 128/128 conformes à la matrice
- tué · l.69 · supprimer · règle supprimée — • owner / Repair / état « pending » → « in_progress » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.69 · élargir · « auth().role == 'owner' » remplacé par « auth() != null » — 128/128 conformes à la matrice
- survivant · l.69 · oublier une condition · condition « auth().role == 'owner' » retirée — 128/128 conformes à la matrice
- tué · l.69 · oublier une condition · condition « before().status == pending » retirée — • owner / Repair / état « in_progress » → « refused » : attendu REFUSÉ, obtenu PERMIS
- tué · l.69 · oublier une condition · condition « (status == in_progress || status == refused) » retirée — • owner / Repair / état « pending » → « done » : attendu REFUSÉ, obtenu PERMIS
- tué · l.69 · oublier une condition · condition « description == before().description » retirée — • owner / Repair / étape « pending » → « in_progress » en changeant aussi description : attendu REFUSÉ, obtenu PERMIS
- tué · l.69 · oublier une condition · condition « vehicleId == before().vehicleId » retirée — • owner / Repair / étape « pending » → « in_progress » en changeant aussi vehicleId : attendu REFUSÉ, obtenu PERMIS
- tué · l.70 · supprimer · règle supprimée — • owner / Repair / état « in_progress » → « done » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.70 · élargir · « auth().role == 'owner' » remplacé par « auth() != null » — 128/128 conformes à la matrice
- survivant · l.70 · oublier une condition · condition « auth().role == 'owner' » retirée — 128/128 conformes à la matrice
- tué · l.70 · oublier une condition · condition « before().status == in_progress » retirée — • owner / Repair / état « pending » → « done » : attendu REFUSÉ, obtenu PERMIS
- tué · l.70 · oublier une condition · condition « status == done » retirée — • owner / Repair / état « in_progress » → « pending » : attendu REFUSÉ, obtenu PERMIS
- tué · l.70 · oublier une condition · condition « description == before().description » retirée — • owner / Repair / étape « in_progress » → « done » en changeant aussi description : attendu REFUSÉ, obtenu PERMIS
- tué · l.70 · oublier une condition · condition « vehicleId == before().vehicleId » retirée — • owner / Repair / étape « in_progress » → « done » en changeant aussi vehicleId : attendu REFUSÉ, obtenu PERMIS
- tué · l.71 · supprimer · règle supprimée — • owner / Repair / étape « pending » → « in_progress » en changeant aussi ownerId : attendu REFUSÉ, obtenu PERMIS