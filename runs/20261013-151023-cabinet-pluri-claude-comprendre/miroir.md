# Gestion du cabinet — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, Le professionnel), 4 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : Dossiers, Rendez-vous, Factures, Devis

## Le professionnel (invité par administrateur)
- Ne voit rien

## Les informations de chaque fiche

- **Dossier** : Nom du dossier (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Date de naissance (date) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long) · ☐ Notes (texte long)
- **Rendez-vous** : Objet du rendez-vous (texte court) ◦ choisi par nous
  - relié à : Dossier
  - proposé (à cocher) : ☐ Date et heure (date et heure) · ☐ Durée (minutes) (nombre) · ☐ Professionnel (texte court) · ☐ Notes (texte long)
- **Facture** : Numéro de facture (texte court) ◦ choisi par nous
  - relié à : Dossier
  - proposé (à cocher) : ☐ Date de facture (date) · ☐ Montant total (montant) · ☐ Description des prestations (texte long) · ☐ Date d'échéance (date) · ☐ Mode de paiement (texte court)
- **Devis** : Numéro du devis (texte court) ◦ choisi par nous
  - relié à : Dossier
  - proposé (à cocher) : ☐ Montant total (montant) · ☐ Description des prestations (texte long) · ☐ Date de validité (date)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Dossier → « Nom du dossier » · Rendez-vous → « Objet du rendez-vous » · Facture → « Numéro de facture » · Devis → « Numéro du devis »

## Pas encore dans notre stock (vos mots)

- Agenda et gestion des rendez-vous — « gestion de rdv... avec agenda »
- Facturation — « avec agenda, facturation »
- Devis — « facturation et devis »
- Partage des dossiers, un par un, par l'administrateur avec les professionnels concernés — « l'administrateur pourra partager les dossiers avec les professionnels concernés »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Dossier:nom` = oui | <nouveau nom>  (Dossier → « Nom du dossier »)
- `nom:RendezVous:objet` = oui | <nouveau nom>  (Rendez-vous → « Objet du rendez-vous »)
- `nom:Facture:numero` = oui | <nouveau nom>  (Facture → « Numéro de facture »)
- `nom:Devis:numero` = oui | <nouveau nom>  (Devis → « Numéro du devis »)
- `garder:Dossier:Prénom` = oui | non
- `garder:Dossier:Date de naissance` = oui | non
- `garder:Dossier:Téléphone` = oui | non
- `garder:Dossier:Email` = oui | non
- `garder:Dossier:Adresse` = oui | non
- `garder:Dossier:Notes` = oui | non
- `garder:RendezVous:Date et heure` = oui | non
- `garder:RendezVous:Durée (minutes)` = oui | non
- `garder:RendezVous:Professionnel` = oui | non
- `garder:RendezVous:Notes` = oui | non
- `garder:Facture:Date de facture` = oui | non
- `garder:Facture:Montant total` = oui | non
- `garder:Facture:Description des prestations` = oui | non
- `garder:Facture:Date d'échéance` = oui | non
- `garder:Facture:Mode de paiement` = oui | non
- `garder:Devis:Montant total` = oui | non
- `garder:Devis:Description des prestations` = oui | non
- `garder:Devis:Date de validité` = oui | non

### Pourquoi chaque droit

- administrateur / Dossier : tient le registre (supprimer : seulement si le brief le dit) — « l'administrateur pourra partager les dossiers avec les professionnels concernés afin d'assurer une confidentialité des données »
- administrateur / RendezVous : tient le registre (supprimer : seulement si le brief le dit) — « Logiciel multi-utilisateurs de gestion de rdv »
- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « avec agenda, facturation et devis »
- administrateur / Devis : tient le registre (supprimer : seulement si le brief le dit) — « gestion de rdv, facturation et devis »
