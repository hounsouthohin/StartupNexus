# Mutants — atelier-partage

50 mutants · 0 invalides (le schéma ne compile plus) · 50 valides
**Tués : 40/50 (80 %)** · survivants : 10 · plantages : 0

## Survivants et plantages (à examiner)

- **survivant** l.49 — oublier une condition : condition « check(workshop) » retirée
  `@@allow('read', auth() != null)`
  123/123 conformes à la matrice
- **survivant** l.62 — élargir : « auth().role == 'participant' » remplacé par « auth() != null »
  `@@allow('read,update', auth() != null && userId == auth().id)`
  123/123 conformes à la matrice
- **survivant** l.62 — oublier une condition : condition « auth().role == 'participant' » retirée
  `@@allow('read,update', userId == auth().id)`
  123/123 conformes à la matrice
- **survivant** l.84 — élargir : « auth().role == 'participant' » remplacé par « auth() != null »
  `@@allow('read', auth() != null && ownerId == auth().id)`
  123/123 conformes à la matrice
- **survivant** l.84 — oublier une condition : condition « auth().role == 'participant' » retirée
  `@@allow('read', ownerId == auth().id)`
  123/123 conformes à la matrice
- **survivant** l.87 — élargir : « auth().role == 'animateur' » remplacé par « auth() != null »
  `@@allow('update', auth() != null)`
  123/123 conformes à la matrice
- **survivant** l.88 — élargir : « auth().role == 'animateur' » remplacé par « auth() != null »
  `@@allow('post-update', auth() != null && before().status == pending && (status == confirmed || status == cancelled) && slotId == before().slotId && comment == before().comment)`
  123/123 conformes à la matrice
- **survivant** l.88 — oublier une condition : condition « auth().role == 'animateur' » retirée
  `@@allow('post-update', before().status == pending && (status == confirmed || status == cancelled) && slotId == before().slotId && comment == before().comment)`
  123/123 conformes à la matrice
- **survivant** l.89 — élargir : « auth().role == 'animateur' » remplacé par « auth() != null »
  `@@allow('post-update', auth() != null && before().status == confirmed && status == done && slotId == before().slotId && comment == before().comment)`
  123/123 conformes à la matrice
- **survivant** l.89 — oublier une condition : condition « auth().role == 'animateur' » retirée
  `@@allow('post-update', before().status == confirmed && status == done && slotId == before().slotId && comment == before().comment)`
  123/123 conformes à la matrice

## Tous les mutants

- tué · l.27 · supprimer · règle supprimée — • visitor / Workshop / voir : toutes (0/1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.28 · supprimer · règle supprimée — • animateur / Workshop / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.28 · élargir · « auth().role == 'animateur' » remplacé par « auth() != null » — • participant / Workshop / créer : attendu REFUSÉ, obtenu PERMIS
- tué · l.37 · supprimer · règle supprimée — • participant / Domain / voir : toutes (1/2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.38 · supprimer · règle supprimée — • visitor / Domain / voir : seulement au travers de Workshop (0, attendu 0) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.49 · supprimer · règle supprimée — • participant / Slot / voir : toutes (0/2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.49 · oublier une condition · condition « auth() != null » retirée — • visitor / Slot / voir : rien (2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- survivant · l.49 · oublier une condition · condition « check(workshop) » retirée — 123/123 conformes à la matrice
- tué · l.50 · supprimer · règle supprimée — • animateur / Slot / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.61 · supprimer · règle supprimée — • participant / ParticipantProfile / créer : son propre profil (première connexion) : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.61 · élargir · « auth().role == 'participant' » remplacé par « auth() != null » — • animateur / ParticipantProfile / créer : un profil (pas son rôle) : attendu REFUSÉ, obtenu PERMIS
- tué · l.61 · oublier une condition · condition « auth().role == 'participant' » retirée — • animateur / ParticipantProfile / créer : un profil (pas son rôle) : attendu REFUSÉ, obtenu PERMIS
- tué · l.61 · oublier une condition · condition « userId == auth().id » retirée — • participant / ParticipantProfile / créer : le profil de quelqu'un d'autre : attendu REFUSÉ, obtenu PERMIS
- tué · l.62 · supprimer · règle supprimée — • participant / ParticipantProfile / voir : les siennes seulement (0, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- survivant · l.62 · élargir · « auth().role == 'participant' » remplacé par « auth() != null » — 123/123 conformes à la matrice
- survivant · l.62 · oublier une condition · condition « auth().role == 'participant' » retirée — 123/123 conformes à la matrice
- tué · l.62 · oublier une condition · condition « userId == auth().id » retirée — • participant / ParticipantProfile / voir : les siennes seulement (3, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.63 · supprimer · règle supprimée — • animateur / ParticipantProfile / voir : seulement au travers de Reservation (0, attendu 0) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.63 · élargir · « auth().role == 'animateur' » remplacé par « auth() != null » — • participant / ParticipantProfile / voir : les siennes seulement (2, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.63 · oublier une condition · condition « auth().role == 'animateur' » retirée — • visitor / ParticipantProfile / voir : rien (2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.63 · oublier une condition · condition « reservations?[true] » retirée — • animateur / ParticipantProfile / voir : seulement au travers de Reservation (3, attendu 2) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.64 · supprimer · règle supprimée — • participant / ParticipantProfile / modifier : changer le propriétaire : attendu REFUSÉ, obtenu PERMIS
- tué · l.84 · supprimer · règle supprimée — • participant / Reservation / voir : les siennes seulement (0, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- survivant · l.84 · élargir · « auth().role == 'participant' » remplacé par « auth() != null » — 123/123 conformes à la matrice
- survivant · l.84 · oublier une condition · condition « auth().role == 'participant' » retirée — 123/123 conformes à la matrice
- tué · l.84 · oublier une condition · condition « ownerId == auth().id » retirée — • participant / Reservation / voir : les siennes seulement (2, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.85 · supprimer · règle supprimée — • animateur / ParticipantProfile / voir : seulement au travers de Reservation (2, attendu 0) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.85 · élargir · « auth().role == 'animateur' » remplacé par « auth() != null » — • participant / Reservation / voir : les siennes seulement (2, attendu 1) : attendu PERMIS, obtenu REFUSÉ (undefined)
- tué · l.86 · supprimer · règle supprimée — • participant / Reservation / créer : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- tué · l.86 · élargir · « auth().role == 'participant' » remplacé par « auth() != null » — • animateur / Reservation / créer : à son propre nom : attendu REFUSÉ, obtenu REFUSÉ (ERREUR : Failed to execute query: error: insert or update on table "Reservation" violates foreign key constraint "Reservation_ownerId_fkey")
- tué · l.86 · oublier une condition · condition « auth().role == 'participant' » retirée — • animateur / Reservation / créer : à son propre nom : attendu REFUSÉ, obtenu REFUSÉ (ERREUR : Failed to execute query: error: insert or update on table "Reservation" violates foreign key constraint "Reservation_ownerId_fkey")
- tué · l.86 · oublier une condition · condition « ownerId == auth().id » retirée — • participant / Reservation / créer : au nom d'un autre participant : attendu REFUSÉ, obtenu PERMIS
- tué · l.86 · oublier une condition · condition « status == pending » retirée — • participant / Reservation / créer : directement « confirmed » : attendu REFUSÉ, obtenu PERMIS
- tué · l.87 · supprimer · règle supprimée — • animateur / Reservation / état « pending » → « confirmed » : attendu PERMIS, obtenu REFUSÉ (not-found)
- survivant · l.87 · élargir · « auth().role == 'animateur' » remplacé par « auth() != null » — 123/123 conformes à la matrice
- tué · l.88 · supprimer · règle supprimée — • animateur / Reservation / état « pending » → « confirmed » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.88 · élargir · « auth().role == 'animateur' » remplacé par « auth() != null » — 123/123 conformes à la matrice
- survivant · l.88 · oublier une condition · condition « auth().role == 'animateur' » retirée — 123/123 conformes à la matrice
- tué · l.88 · oublier une condition · condition « before().status == pending » retirée — • animateur / Reservation / état « confirmed » → « cancelled » : attendu REFUSÉ, obtenu PERMIS
- tué · l.88 · oublier une condition · condition « (status == confirmed || status == cancelled) » retirée — • animateur / Reservation / état « pending » → « done » : attendu REFUSÉ, obtenu PERMIS
- tué · l.88 · oublier une condition · condition « slotId == before().slotId » retirée — • animateur / Reservation / étape « pending » → « confirmed » en changeant aussi slotId : attendu REFUSÉ, obtenu PERMIS
- tué · l.88 · oublier une condition · condition « comment == before().comment » retirée — • animateur / Reservation / étape « pending » → « confirmed » en changeant aussi comment : attendu REFUSÉ, obtenu PERMIS
- tué · l.89 · supprimer · règle supprimée — • animateur / Reservation / état « confirmed » → « done » : attendu PERMIS, obtenu REFUSÉ (rejected-by-policy)
- survivant · l.89 · élargir · « auth().role == 'animateur' » remplacé par « auth() != null » — 123/123 conformes à la matrice
- survivant · l.89 · oublier une condition · condition « auth().role == 'animateur' » retirée — 123/123 conformes à la matrice
- tué · l.89 · oublier une condition · condition « before().status == confirmed » retirée — • animateur / Reservation / état « pending » → « done » : attendu REFUSÉ, obtenu PERMIS
- tué · l.89 · oublier une condition · condition « status == done » retirée — • animateur / Reservation / état « confirmed » → « pending » : attendu REFUSÉ, obtenu PERMIS
- tué · l.89 · oublier une condition · condition « slotId == before().slotId » retirée — • animateur / Reservation / étape « confirmed » → « done » en changeant aussi slotId : attendu REFUSÉ, obtenu PERMIS
- tué · l.89 · oublier une condition · condition « comment == before().comment » retirée — • animateur / Reservation / étape « confirmed » → « done » en changeant aussi comment : attendu REFUSÉ, obtenu PERMIS
- tué · l.90 · supprimer · règle supprimée — • animateur / Reservation / étape « pending » → « confirmed » en changeant aussi ownerId : attendu REFUSÉ, obtenu PERMIS