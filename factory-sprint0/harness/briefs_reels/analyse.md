# Vrais briefs — ce que l'usine en fait (4 oct 2026)

## 1. L'usine actuelle (avant la matrice) sur ces 5 briefs

| Brief | Compile ? | Cause | Où |
|---|---|---|---|
| agence-reservations | ❌ | clé étrangère facultative (`managerId String?`) mais relation rendue obligatoire | générateur du schéma (injection des relations) |
| maintenance-interventions | ❌ | même cause (`technicianId`) | idem |
| salle-de-sport | ❌ | `userId` dans le filtre d'une entité globale (`Course`) | propriétaire calculé à deux endroits (panne connue) |
| sav-depannage | ❌ | valeurs d'enum « 478 / 754 / 775 » : Prisma interdit un nom commençant par un chiffre | générateur du schéma |
| gestion-scolaire | ❌ | relation vers un modèle `Student` jamais déclaré | aucune vérification à la frontière architect → génération (règle 3) |

**0/5.** Aucune de ces causes n'était apparue sur nos propres briefs.

Le miroir actuel **sous-déclare** les manques : il voit SMS et Google Agenda, mais rate paiement
Stripe et renouvellement automatique (salle de sport), rappels « la veille / le jour J », e-mails
générés, acceptation par mail (maintenance), « le gestionnaire gère SES prestataires » (agence).

## 2. Ce que couvrirait la matrice D1 — chaque exigence classée à la main

| Brief | D1 (qui voit / fait quoi) | D2 (relations) | D4 (effets : e-mail, SMS, paiement, intégrations, PDF) | D5 (temps) | Présentation (planning, carte, impression) | Hors périmètre |
|---|---|---|---|---|---|---|
| agence | 7 | 1 (ses prestataires) | 2 (alertes, Google Agenda) | — | — | — |
| maintenance | 5 | — | 5 (mails du planning, factures PDF envoyées, acceptation par mail, SMS, envoi du livrable) | 1 (rappels) | 2 (planning, carte) | 3 (mobile, pièces jointes, données en interne) |
| salle de sport | 5 | — | 2 (paiement Stripe/PayPal, renouvellement) | 2 (renouvellement, rappels) | 1 (calendrier des cours) | — |
| sav-depannage | 5 | — | — | — | 2 (impressions, planning) | — |
| gestion-scolaire | ~4 (rôles, absences, notes) | plusieurs (le parent voit SON enfant) | 1 (frais de scolarité) | — | 2 (emploi du temps, agenda) | messagerie, forum, ressources numériques… (trop vaste) |

Part de chaque brief que D1 porterait seule : environ **70 %** (agence, dépannage), **50 %**
(salle de sport), **30 %** (maintenance), **faible** (école, demande démesurée).

## 3. Ce que ça change

- **D4 (effets) apparaît dans 4 briefs réels sur 5** — dans nos propres briefs, une ou deux fois.
  L'ordre « D2 → D3 → D4 → D5 » était supposé ; la demande réelle place les effets
  (e-mails de notification, paiement) juste après D1.
- **La « présentation » revient souvent** (planning, calendrier, impressions) : ce sont les
  « blocs » prévus pour l'IA des pages uniques — une vue calendrier compilée servirait 4 briefs sur 5.
- **La frontière architect → génération doit refuser** un modèle qui référence un modèle absent
  (règle 3) ; le générateur du schéma doit traiter les valeurs d'enum numériques et l'optionalité
  des relations. Ce sont des défauts du cœur, révélés seulement par des données réelles.
- Le miroir doit vérifier chaque axe (effets, temps, présentation) au lieu de résumer librement.
