# Gestion de cabinet — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, Le professionnel concerné), 4 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : rendez-vous, factures, devis, dossiers

## Le professionnel concerné (invité par administrateur)
- Ne voit rien

## Les informations de chaque fiche

- **Rendez-vous** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date et heure du rendez-vous (date et heure) · ☐ Durée (nombre) · ☐ Motif (texte court)
- **Facture** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Numéro de facture (texte court) · ☐ Date de facture (date) · ☐ Montant total (montant)
- **Devis** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Numéro de devis (texte court) · ☐ Date du devis (date) · ☐ Montant total (montant)
- **Dossier** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long) · ☐ Niveau de confidentialité (texte court)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : rendez-vous → « Intitulé » · facture → « Intitulé » · devis → « Intitulé » · dossier → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Gestion de rendez-vous / agenda — « gestion de rdv »
- Agenda — « avec agenda »
- Facturation — « facturation »
- Devis — « devis »
- Partage fin des dossiers avec certains professionnels — « l'administrateur pourra partager les dossiers avec les professionnels concernés »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:RendezVous:intitule` = oui | <nouveau nom>  (rendez-vous → « Intitulé »)
- `nom:Facture:intitule` = oui | <nouveau nom>  (facture → « Intitulé »)
- `nom:Devis:intitule` = oui | <nouveau nom>  (devis → « Intitulé »)
- `nom:Dossier:intitule` = oui | <nouveau nom>  (dossier → « Intitulé »)
- `garder:RendezVous:Date et heure du rendez-vous` = oui | non
- `garder:RendezVous:Durée` = oui | non
- `garder:RendezVous:Motif` = oui | non
- `garder:Facture:Numéro de facture` = oui | non
- `garder:Facture:Date de facture` = oui | non
- `garder:Facture:Montant total` = oui | non
- `garder:Devis:Numéro de devis` = oui | non
- `garder:Devis:Date du devis` = oui | non
- `garder:Devis:Montant total` = oui | non
- `garder:Dossier:Description` = oui | non
- `garder:Dossier:Niveau de confidentialité` = oui | non

### Pourquoi chaque droit

- administrateur / RendezVous : tient le registre (supprimer : seulement si le brief le dit) — « gestion de rdv »
- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « facturation »
- administrateur / Devis : tient le registre (supprimer : seulement si le brief le dit) — « devis »
- administrateur / Dossier : tient le registre (supprimer : seulement si le brief le dit) — « l'administrateur pourra partager les dossiers avec les professionnels concernés »
