# Mutants — agence-reservations

70 mutants · 0 invalides (le schéma ne compile plus) · 70 valides
**Tués : 54/70 (77.1 %)** · survivants : 16 · plantages : 0

## Survivants et plantages (à examiner)

- **survivant** l.48 — élargir : « auth().role == 'prestataire' » remplacé par « auth() != null »
  `@@allow('read,update', auth() != null && userId == auth().id)`
  119/119 conformes à la matrice
- **survivant** l.48 — oublier une condition : condition « auth().role == 'prestataire' » retirée
  `@@allow('read,update', userId == auth().id)`
  119/119 conformes à la matrice
- **survivant** l.85 — élargir : « auth().role == 'prestataire' » remplacé par « auth() != null »
  `@@allow('read', auth() != null || auth().role == 'gestionnaire' || auth().role == 'admin')`
  119/119 conformes à la matrice
- **survivant** l.85 — élargir : « auth().role == 'gestionnaire' » remplacé par « auth() != null »
  `@@allow('read', auth().role == 'prestataire' || auth() != null || auth().role == 'admin')`
  119/119 conformes à la matrice
- **survivant** l.85 — élargir : « auth().role == 'admin' » remplacé par « auth() != null »
  `@@allow('read', auth().role == 'prestataire' || auth().role == 'gestionnaire' || auth() != null)`
  119/119 conformes à la matrice
- **survivant** l.87 — oublier une condition : condition « check(destination, 'read') » retirée
  `@@allow('create', (auth().role == 'prestataire' || auth().role == 'gestionnaire') && ownerId == auth().id && status == open && check(customer, 'read') && check(rate, 'read'))`
  119/119 conformes à la matrice
- **survivant** l.87 — oublier une condition : condition « check(rate, 'read') » retirée
  `@@allow('create', (auth().role == 'prestataire' || auth().role == 'gestionnaire') && ownerId == auth().id && status == open && check(customer, 'read') && check(destination, 'read'))`
  119/119 conformes à la matrice
- **survivant** l.88 — élargir : « auth().role == 'prestataire' » remplacé par « auth() != null »
  `@@allow('update', auth() != null || auth().role == 'gestionnaire' || auth().role == 'admin')`
  119/119 conformes à la matrice
- **survivant** l.88 — élargir : « auth().role == 'gestionnaire' » remplacé par « auth() != null »
  `@@allow('update', auth().role == 'prestataire' || auth() != null || auth().role == 'admin')`
  119/119 conformes à la matrice
- **survivant** l.88 — élargir : « auth().role == 'admin' » remplacé par « auth() != null »
  `@@allow('update', auth().role == 'prestataire' || auth().role == 'gestionnaire' || auth() != null)`
  119/119 conformes à la matrice
- **survivant** l.90 — élargir : « auth().role == 'prestataire' » remplacé par « auth() != null »
  `@@allow('post-update', (auth() != null || auth().role == 'gestionnaire' || auth().role == 'admin') && ((before().status == open && status == open) || (before().status == closed && status == closed)))`
  119/119 conformes à la matrice
- **survivant** l.90 — élargir : « auth().role == 'gestionnaire' » remplacé par « auth() != null »
  `@@allow('post-update', (auth().role == 'prestataire' || auth() != null || auth().role == 'admin') && ((before().status == open && status == open) || (before().status == closed && status == closed)))`
  119/119 conformes à la matrice
- **survivant** l.90 — élargir : « auth().role == 'admin' » remplacé par « auth() != null »
  `@@allow('post-update', (auth().role == 'prestataire' || auth().role == 'gestionnaire' || auth() != null) && ((before().status == open && status == open) || (before().status == closed && status == closed)))`
  119/119 conformes à la matrice
- **survivant** l.90 — oublier une condition : condition « (auth().role == 'prestataire' || auth().role == 'gestionnaire' || auth().role == 'admin') » retirée
  `@@allow('post-update', ((before().status == open && status == open) || (before().status == closed && status == closed)))`
  119/119 conformes à la matrice
- **survivant** l.92 — oublier une condition : condition « before().status == open » retirée
  `@@allow('post-update', auth().role == 'gestionnaire' && status == closed && note == before().note && customerId == before().customerId && destinationId == before().destinationId && rateId == before().rateId)`
  119/119 conformes à la matrice
- **survivant** l.92 — oublier une condition : condition « status == closed » retirée
  `@@allow('post-update', auth().role == 'gestionnaire' && before().status == open && note == before().note && customerId == before().customerId && destinationId == before().destinationId && rateId == before().rateId)`
  119/119 conformes à la matrice

## Tous les mutants

- tué · l.27 · supprimer · règle supprimée — • admin / Rate / voir : toutes (0/2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.28 · supprimer · règle supprimée — • admin / Rate / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.28 · élargir · « auth().role == 'admin' » remplacé par « auth() != null » — • prestataire / Rate / créer : attendu REFUSÉ, obtenu PERMIS
- tué · l.28 · élargir · « auth().role == 'gestionnaire' » remplacé par « auth() != null » — • prestataire / Rate / créer : attendu REFUSÉ, obtenu PERMIS
- tué · l.36 · supprimer · règle supprimée — • admin / Destination / voir : toutes (0/2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.37 · supprimer · règle supprimée — • admin / Destination / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.37 · élargir · « auth().role == 'admin' » remplacé par « auth() != null » — • prestataire / Destination / créer : attendu REFUSÉ, obtenu PERMIS
- tué · l.37 · élargir · « auth().role == 'gestionnaire' » remplacé par « auth() != null » — • prestataire / Destination / créer : attendu REFUSÉ, obtenu PERMIS
- tué · l.47 · supprimer · règle supprimée — • prestataire / ProviderProfile / créer : son propre profil (première connexion) : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.47 · élargir · « auth().role == 'prestataire' » remplacé par « auth() != null » — • admin / ProviderProfile / créer : un profil (pas son rôle) : attendu REFUSÉ, obtenu PERMIS
- tué · l.47 · oublier une condition · condition « auth().role == 'prestataire' » retirée — • admin / ProviderProfile / créer : un profil (pas son rôle) : attendu REFUSÉ, obtenu PERMIS
- tué · l.47 · oublier une condition · condition « userId == auth().id » retirée — • prestataire / ProviderProfile / créer : le profil de quelqu'un d'autre : attendu REFUSÉ, obtenu PERMIS
- tué · l.48 · supprimer · règle supprimée — • prestataire / ProviderProfile / voir : les siennes seulement (0, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- survivant · l.48 · élargir · « auth().role == 'prestataire' » remplacé par « auth() != null » — 119/119 conformes à la matrice
- survivant · l.48 · oublier une condition · condition « auth().role == 'prestataire' » retirée — 119/119 conformes à la matrice
- tué · l.48 · oublier une condition · condition « userId == auth().id » retirée — • prestataire / ProviderProfile / voir : les siennes seulement (2, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.49 · supprimer · règle supprimée — • admin / ProviderProfile / voir : toutes (0/2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.49 · élargir · « auth().role == 'gestionnaire' » remplacé par « auth() != null » — • prestataire / ProviderProfile / voir : les siennes seulement (2, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.49 · élargir · « auth().role == 'admin' » remplacé par « auth() != null » — • prestataire / ProviderProfile / voir : les siennes seulement (2, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.50 · supprimer · règle supprimée — • admin / ProviderProfile / modifier : changer le propriétaire : attendu REFUSÉ, obtenu PERMIS
- tué · l.60 · supprimer · règle supprimée — • prestataire / Customer / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.60 · élargir · « auth().role == 'prestataire' » remplacé par « auth() != null » — • admin / Customer / créer : à son propre nom : attendu REFUSÉ, obtenu PERMIS
- tué · l.60 · oublier une condition · condition « auth().role == 'prestataire' » retirée — • admin / Customer / créer : à son propre nom : attendu REFUSÉ, obtenu PERMIS
- tué · l.60 · oublier une condition · condition « ownerId == auth().id » retirée — • prestataire / Customer / créer : au nom d'un autre prestataire : attendu REFUSÉ, obtenu PERMIS
- tué · l.61 · supprimer · règle supprimée — • prestataire / Customer / voir : les siennes seulement (0, attendu 2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.61 · élargir · « auth().role == 'prestataire' » remplacé par « auth() != null » — • gestionnaire / Customer / modifier : sa fiche d'avant un changement de rôle : attendu REFUSÉ, obtenu PERMIS
- tué · l.61 · oublier une condition · condition « auth().role == 'prestataire' » retirée — • gestionnaire / Customer / modifier : sa fiche d'avant un changement de rôle : attendu REFUSÉ, obtenu PERMIS
- tué · l.61 · oublier une condition · condition « ownerId == auth().id » retirée — • prestataire / Customer / voir : les siennes seulement (3, attendu 2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.62 · supprimer · règle supprimée — • admin / Customer / voir : toutes (0/3) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.62 · élargir · « auth().role == 'admin' » remplacé par « auth() != null » — • gestionnaire / Customer / voir : seulement au travers de Reservation (3, attendu 2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.63 · supprimer · règle supprimée — • gestionnaire / Customer / voir : seulement au travers de Reservation (0, attendu 0) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.63 · élargir · « auth().role == 'gestionnaire' » remplacé par « auth() != null » — • prestataire / Customer / voir : les siennes seulement (3, attendu 2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.63 · oublier une condition · condition « auth().role == 'gestionnaire' » retirée — • visitor / Customer / voir : rien (2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.63 · oublier une condition · condition « reservations?[true] » retirée — • gestionnaire / Customer / voir : seulement au travers de Reservation (3, attendu 2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.64 · supprimer · règle supprimée — • admin / Customer / modifier : changer le propriétaire : attendu REFUSÉ, obtenu PERMIS
- tué · l.85 · supprimer · règle supprimée — • admin / Reservation / voir : toutes (0/3) : attendu PERMIS, obtenu REFUSÉ (undefined)
- survivant · l.85 · élargir · « auth().role == 'prestataire' » remplacé par « auth() != null » — 119/119 conformes à la matrice
- survivant · l.85 · élargir · « auth().role == 'gestionnaire' » remplacé par « auth() != null » — 119/119 conformes à la matrice
- survivant · l.85 · élargir · « auth().role == 'admin' » remplacé par « auth() != null » — 119/119 conformes à la matrice
- tué · l.87 · supprimer · règle supprimée — • gestionnaire / Reservation / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.87 · élargir · « auth().role == 'prestataire' » remplacé par « auth() != null » — • admin / Reservation / créer : à son propre nom : attendu REFUSÉ, obtenu PERMIS
- tué · l.87 · élargir · « auth().role == 'gestionnaire' » remplacé par « auth() != null » — • admin / Reservation / créer : à son propre nom : attendu REFUSÉ, obtenu PERMIS
- tué · l.87 · oublier une condition · condition « (auth().role == 'prestataire' || auth().role == 'gestionnaire') » retirée — • admin / Reservation / créer : à son propre nom : attendu REFUSÉ, obtenu PERMIS
- tué · l.87 · oublier une condition · condition « ownerId == auth().id » retirée — • gestionnaire / Reservation / créer : au nom d'un autre gestionnaire : attendu REFUSÉ, obtenu PERMIS
- tué · l.87 · oublier une condition · condition « status == open » retirée — • gestionnaire / Reservation / créer : directement « closed » : attendu REFUSÉ, obtenu PERMIS
- tué · l.87 · oublier une condition · condition « check(customer, 'read') » retirée — • gestionnaire / Reservation / créer : en pointant Customer qu'il ne voit pas : attendu REFUSÉ, obtenu PERMIS
- survivant · l.87 · oublier une condition · condition « check(destination, 'read') » retirée — 119/119 conformes à la matrice
- survivant · l.87 · oublier une condition · condition « check(rate, 'read') » retirée — 119/119 conformes à la matrice
- tué · l.88 · supprimer · règle supprimée — • admin / Reservation / modifier en « open » : attendu PERMIS, obtenu REFUSÉ (not-found)
- survivant · l.88 · élargir · « auth().role == 'prestataire' » remplacé par « auth() != null » — 119/119 conformes à la matrice
- survivant · l.88 · élargir · « auth().role == 'gestionnaire' » remplacé par « auth() != null » — 119/119 conformes à la matrice
- survivant · l.88 · élargir · « auth().role == 'admin' » remplacé par « auth() != null » — 119/119 conformes à la matrice
- tué · l.90 · supprimer · règle supprimée — • admin / Reservation / modifier en « open » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.90 · élargir · « auth().role == 'prestataire' » remplacé par « auth() != null » — 119/119 conformes à la matrice
- survivant · l.90 · élargir · « auth().role == 'gestionnaire' » remplacé par « auth() != null » — 119/119 conformes à la matrice
- survivant · l.90 · élargir · « auth().role == 'admin' » remplacé par « auth() != null » — 119/119 conformes à la matrice
- survivant · l.90 · oublier une condition · condition « (auth().role == 'prestataire' || auth().role == 'gestionnaire' || auth().role == 'admin') » retirée — 119/119 conformes à la matrice
- tué · l.90 · oublier une condition · condition « ((before().status == open && status == open) || (before().status == closed && status == closed)) » retirée — • admin / Reservation / état « open » → « closed » : attendu REFUSÉ, obtenu PERMIS
- tué · l.92 · supprimer · règle supprimée — • gestionnaire / Reservation / état « open » → « closed » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.92 · élargir · « auth().role == 'gestionnaire' » remplacé par « auth() != null » — • admin / Reservation / état « open » → « closed » : attendu REFUSÉ, obtenu PERMIS
- tué · l.92 · oublier une condition · condition « auth().role == 'gestionnaire' » retirée — • admin / Reservation / état « open » → « closed » : attendu REFUSÉ, obtenu PERMIS
- survivant · l.92 · oublier une condition · condition « before().status == open » retirée — 119/119 conformes à la matrice
- survivant · l.92 · oublier une condition · condition « status == closed » retirée — 119/119 conformes à la matrice
- tué · l.92 · oublier une condition · condition « note == before().note » retirée — • gestionnaire / Reservation / étape « open » → « closed » en changeant aussi note : attendu REFUSÉ, obtenu PERMIS
- tué · l.92 · oublier une condition · condition « customerId == before().customerId » retirée — • gestionnaire / Reservation / étape « open » → « closed » en changeant aussi customerId : attendu REFUSÉ, obtenu PERMIS
- tué · l.92 · oublier une condition · condition « destinationId == before().destinationId » retirée — • gestionnaire / Reservation / étape « open » → « closed » en changeant aussi destinationId : attendu REFUSÉ, obtenu PERMIS
- tué · l.92 · oublier une condition · condition « rateId == before().rateId » retirée — • gestionnaire / Reservation / étape « open » → « closed » en changeant aussi rateId : attendu REFUSÉ, obtenu PERMIS
- tué · l.93 · supprimer · règle supprimée — • prestataire / Reservation / supprimer : attendu PERMIS, obtenu REFUSÉ (not-found)
- tué · l.93 · élargir · « auth().role == 'prestataire' » remplacé par « auth() != null » — • admin / Reservation / supprimer : attendu REFUSÉ, obtenu PERMIS
- tué · l.94 · supprimer · règle supprimée — • admin / Reservation / modifier : changer le propriétaire : attendu REFUSÉ, obtenu PERMIS