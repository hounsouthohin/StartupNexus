# Gestion du cabinet — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, Le professionnel), 5 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : Dossiers, Rendez-vous, Factures, Devis

## Le professionnel (invité par administrateur)
- a son Professionnel, créé automatiquement, qu'il peut modifier

## Les informations de chaque fiche

- **Professionnel** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Spécialité (texte court) · ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Dossier** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Date de naissance (date) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long) · ☐ Notes (texte long)
- **Rendez-vous** : Objet (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date et heure (date et heure) · ☐ Durée (nombre) · ☐ Lieu ou salle (texte court) · ☐ Notes (texte long)
- **Facture** : Numéro (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date de facture (date) · ☐ Montant (montant) · ☐ Description des prestations (texte long) · ☐ Date de paiement (date) · ☐ Mode de paiement (texte court)
- **Devis** : Numéro (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date du devis (date) · ☐ Montant (montant) · ☐ Description des prestations (texte long) · ☐ Date de validité (date)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Professionnel → « Nom » · Dossier → « Nom » · Rendez-vous → « Objet » · Facture → « Numéro » · Devis → « Numéro »

## Pas encore dans notre stock (vos mots)

- Agenda et gestion des rendez-vous — « gestion de rdv ... avec agenda »
- Facturation (création de factures) — « facturation »
- Établissement de devis — « devis »
- Partage de chaque dossier par l'administrateur avec les seuls professionnels concernés — « l'administrateur pourra partager les dossiers avec les professionnels concernés »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Professionnel:nom` = oui | <nouveau nom>  (Professionnel → « Nom »)
- `nom:Dossier:nom` = oui | <nouveau nom>  (Dossier → « Nom »)
- `nom:RendezVous:objet` = oui | <nouveau nom>  (Rendez-vous → « Objet »)
- `nom:Facture:numero` = oui | <nouveau nom>  (Facture → « Numéro »)
- `nom:Devis:numero` = oui | <nouveau nom>  (Devis → « Numéro »)
- `garder:Professionnel:Prénom` = oui | non
- `garder:Professionnel:Spécialité` = oui | non
- `garder:Professionnel:Email` = oui | non
- `garder:Professionnel:Téléphone` = oui | non
- `garder:Dossier:Prénom` = oui | non
- `garder:Dossier:Date de naissance` = oui | non
- `garder:Dossier:Téléphone` = oui | non
- `garder:Dossier:Email` = oui | non
- `garder:Dossier:Adresse` = oui | non
- `garder:Dossier:Notes` = oui | non
- `garder:RendezVous:Date et heure` = oui | non
- `garder:RendezVous:Durée` = oui | non
- `garder:RendezVous:Lieu ou salle` = oui | non
- `garder:RendezVous:Notes` = oui | non
- `garder:Facture:Date de facture` = oui | non
- `garder:Facture:Montant` = oui | non
- `garder:Facture:Description des prestations` = oui | non
- `garder:Facture:Date de paiement` = oui | non
- `garder:Facture:Mode de paiement` = oui | non
- `garder:Devis:Date du devis` = oui | non
- `garder:Devis:Montant` = oui | non
- `garder:Devis:Description des prestations` = oui | non
- `garder:Devis:Date de validité` = oui | non

### Pourquoi chaque droit

- administrateur / Dossier : tient le registre (supprimer : seulement si le brief le dit) — « l'administrateur pourra partager les dossiers avec les professionnels concernés afin d'assurer une confidentialité des données »
- administrateur / RendezVous : tient le registre (supprimer : seulement si le brief le dit) — « gestion de rdv »
- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « avec agenda, facturation et devis »
- administrateur / Devis : tient le registre (supprimer : seulement si le brief le dit) — « avec agenda, facturation et devis »
- professionnel / Professionnel : préréglage profil : sa propre fiche, créée automatiquement — « les professionnels concernés »
