# Gestion des interventions — ce que l'usine a compris

En bref : 3 rôles (Le dirigeant, L'employé administratif, Le collaborateur), 16 sortes de fiches, 1 circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- les fiches de paie que l'employé administratif saisit pour le collaborateur : pas encore possible — retirées

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## Le dirigeant (responsable de l'app)
- Voit tout : Collaborateurs
- Voit tout, crée et modifie : Clients, Chantiers, Types d'intervention, Bons d'intervention, Matériels, Devis, Catégories de documents, Documents, Codes d'accès
- Voit tout, crée, modifie et supprime : Points de checklist (dans chaque Type d'intervention), Lignes de checklist (dans chaque Bon d'intervention), Lignes de matériel (dans chaque Bon d'intervention)
- Demandes de congés : voit tout, les fait passer de « demandée » à « acceptée » ou « refusée »

## L'employé administratif (invité par dirigeant)
- Voit tout : Collaborateurs
- Voit tout, crée et modifie : Clients, Chantiers, Types d'intervention, Bons d'intervention, Matériels, Devis, Catégories de documents, Documents, Codes d'accès
- Voit tout, crée, modifie et supprime : Points de checklist (dans chaque Type d'intervention), Lignes de checklist (dans chaque Bon d'intervention), Lignes de matériel (dans chaque Bon d'intervention)

## Le collaborateur (invité par dirigeant)
- Voit tout : Clients, Chantiers, Types d'intervention, Points de checklist (dans chaque Type d'intervention), Matériels, Catégories de documents
- Voit tout, crée et modifie : Bons d'intervention, Devis
- Voit tout, crée, modifie et supprime : Lignes de checklist (dans chaque Bon d'intervention), Lignes de matériel (dans chaque Bon d'intervention)
- Voit seulement les siennes et crée : Demandes de congés
- Voit seulement les siennes, crée et modifie : Commandes de matériel, Commandes de vêtements professionnels
- a son Collaborateur, créé automatiquement, qu'il peut modifier

## Les étapes

- La demande de congés commence « demandée » ; de « demandée », vers « acceptée » ou « refusée »
  - Le dirigeant fait passer de « demandée » à « acceptée » ou « refusée »

## Les informations de chaque fiche

- **Collaborateur** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Poste / fonction (texte court)
- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Adresse de facturation (texte long) · ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Chantier** : Adresse (texte court)
  - relié à : Client
  - proposé (à cocher) : ☐ Nom du chantier / site (texte court) · ☐ Contact sur place (texte court) · ☐ Équipements installés (portes, niveleurs de quai) (texte long)
- **Type d'intervention** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long)
- **Point de checklist** : Intitulé du point (texte court) ◦ choisi par nous
  - relié à : dans chaque Type d'intervention
  - proposé (à cocher) : ☐ Ordre d'affichage (nombre) · ☐ Point obligatoire (oui / non)
- **Bon d'intervention** : Début de l'intervention (date et heure) · Fin de l'intervention (date et heure, facultatif) · Signature électronique du client (texte long, facultatif)
  - relié à : Client, Chantier, Collaborateur, Type d'intervention
  - proposé (à cocher) : ☐ Numéro du bon (texte court) · ☐ Compte rendu des travaux (texte long) · ☐ Nom du signataire (texte court)
- **Ligne de checklist** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque Bon d'intervention, Point de checklist
  - proposé (à cocher) : ☐ Fait (oui / non) · ☐ Commentaire (texte long)
- **Matériel** : Désignation (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Référence (texte court) · ☐ Prix unitaire (montant) · ☐ Unité (texte court)
- **Ligne de matériel** : Désignation (texte court) ◦ choisi par nous
  - relié à : dans chaque Bon d'intervention, Matériel
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Prix unitaire appliqué (montant)
- **Devis** : Numéro (texte court) ◦ choisi par nous
  - relié à : Bon d'intervention, Client
  - proposé (à cocher) : ☐ Montant total HT (montant) · ☐ Taux de TVA (nombre) · ☐ Date de validité (date)
- **Catégorie de documents** : Nom (texte court) ◦ choisi par nous
- **Document** : Titre (texte court) ◦ choisi par nous
  - relié à : Catégorie de documents
  - proposé (à cocher) : ☐ Fichier (lien) (lien web) · ☐ Mots-clés (texte court) · ☐ Description (texte long)
- **Demande de congés** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date de début (date) · ☐ Date de fin (date) · ☐ Type de congé (texte court) · ☐ Commentaire (texte long)
- **Commande de matériel** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Matériel
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Date de livraison souhaitée (date)
- **Commande de vêtements professionnels** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Article (texte court) · ☐ Taille (texte court) · ☐ Quantité (nombre)
- **Code d'accès** : Nom (texte court) ◦ choisi par nous · Code (texte court)
  - proposé (à cocher) : ☐ Emplacement du clavier (texte court) · ☐ Date de fin de validité (date)

## Questions

- L'employé administratif verra tous les Clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Chantiers qu'il voit; clôture : choisit les Clients de ses Chantiers
- L'employé administratif verra tous les Chantiers, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Bons d'intervention qu'il voit; clôture : choisit les Chantiers de ses Bons d'intervention
- L'employé administratif verra tous les Bons d'intervention, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Devis qu'il voit; clôture : choisit les Bons d'intervention de ses Devis
- L'employé administratif verra tous les Devis, pas seulement ceux qui le concernent — d'accord ?
- L'employé administratif verra tous les Documents, pas seulement ceux qui le concernent — d'accord ?
- L'employé administratif verra tous les Codes d'accès, pas seulement ceux qui le concernent — d'accord ?
- Le collaborateur verra tous les Clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Bons d'intervention qu'il voit; clôture : choisit les Clients de ses Bons d'intervention
- Le collaborateur verra tous les Chantiers, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Bons d'intervention qu'il voit; clôture : choisit les Chantiers de ses Bons d'intervention
- Le collaborateur verra tous les Bons d'intervention, pas seulement ceux qui le concernent — d'accord ?
- Le collaborateur verra tous les Devis, pas seulement ceux qui le concernent — d'accord ?
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Collaborateur → « Nom » · Client → « Nom » · Type d'intervention → « Intitulé » · Point de checklist → « Intitulé du point » · Ligne de checklist → « Intitulé » · Matériel → « Désignation » · Ligne de matériel → « Désignation » · Devis → « Numéro » · Catégorie de documents → « Nom » · Document → « Titre » · Demande de congés → « Intitulé » · Commande de matériel → « Intitulé » · Commande de vêtements professionnels → « Intitulé » · Code d'accès → « Nom »
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Horodatage précis du début et de la fin de chaque intervention — « Horodatage précis des interventions (début et fin) »
- Ajout automatique du matériel sur l'intervention — « Ajout automatique de matériel »
- Génération instantanée d'un devis à partir du matériel — « génération instantanée de devis »
- Signature électronique du client sur tablette — « Signature électronique du client sur tablette »
- Gestion documentaire avec classement de fichiers — « Gestion documentaire avec classement des fichiers »
- Moteur de recherche dans les documents — « moteur de recherche »
- Stockage sécurisé des fiches de paie (fichiers) pour chaque collaborateur — « Stockage sécurisé des fiches de paie par collaborateur »
- Gestion des codes d'accès des claviers à code : à préciser avec le client s'il s'agit d'enregistrer les codes ou de piloter les claviers (lien avec un objet connecté) — « Gestion des codes d'accès digitaux (clavier à code) »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:employe_administratif:Client` = oui
- `registre_entier:employe_administratif:Chantier` = oui
- `registre_entier:employe_administratif:BonIntervention` = oui
- `registre_entier:employe_administratif:Devis` = oui | non
- `registre_entier:employe_administratif:Document` = oui | non
- `registre_entier:employe_administratif:CodeAcces` = oui | non
- `registre_entier:collaborateur:Client` = oui
- `registre_entier:collaborateur:Chantier` = oui
- `registre_entier:collaborateur:BonIntervention` = oui | non
- `registre_entier:collaborateur:Devis` = oui | non
- `nom:Collaborateur:nom` = oui | <nouveau nom>  (Collaborateur → « Nom »)
- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `nom:TypeIntervention:intitule` = oui | <nouveau nom>  (Type d'intervention → « Intitulé »)
- `nom:PointChecklist:intitule` = oui | <nouveau nom>  (Point de checklist → « Intitulé du point »)
- `nom:LigneChecklist:intitule` = oui | <nouveau nom>  (Ligne de checklist → « Intitulé »)
- `nom:Materiel:designation` = oui | <nouveau nom>  (Matériel → « Désignation »)
- `nom:LigneMateriel:designation` = oui | <nouveau nom>  (Ligne de matériel → « Désignation »)
- `nom:Devis:numero` = oui | <nouveau nom>  (Devis → « Numéro »)
- `nom:CategorieDocument:nom` = oui | <nouveau nom>  (Catégorie de documents → « Nom »)
- `nom:Document:titre` = oui | <nouveau nom>  (Document → « Titre »)
- `nom:DemandeConge:intitule` = oui | <nouveau nom>  (Demande de congés → « Intitulé »)
- `nom:CommandeMateriel:intitule` = oui | <nouveau nom>  (Commande de matériel → « Intitulé »)
- `nom:CommandeVetement:intitule` = oui | <nouveau nom>  (Commande de vêtements professionnels → « Intitulé »)
- `nom:CodeAcces:nom` = oui | <nouveau nom>  (Code d'accès → « Nom »)
- `accepter_proposition` = oui | non
- `garder:Collaborateur:Prénom` = oui | non
- `garder:Collaborateur:Téléphone` = oui | non
- `garder:Collaborateur:Email` = oui | non
- `garder:Collaborateur:Poste / fonction` = oui | non
- `garder:Client:Adresse de facturation` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Chantier:Nom du chantier / site` = oui | non
- `garder:Chantier:Contact sur place` = oui | non
- `garder:Chantier:Équipements installés (portes, niveleurs de quai)` = oui | non
- `garder:TypeIntervention:Description` = oui | non
- `garder:PointChecklist:Ordre d'affichage` = oui | non
- `garder:PointChecklist:Point obligatoire` = oui | non
- `garder:BonIntervention:Numéro du bon` = oui | non
- `garder:BonIntervention:Compte rendu des travaux` = oui | non
- `garder:BonIntervention:Nom du signataire` = oui | non
- `garder:LigneChecklist:Fait` = oui | non
- `garder:LigneChecklist:Commentaire` = oui | non
- `garder:Materiel:Référence` = oui | non
- `garder:Materiel:Prix unitaire` = oui | non
- `garder:Materiel:Unité` = oui | non
- `garder:LigneMateriel:Quantité` = oui | non
- `garder:LigneMateriel:Prix unitaire appliqué` = oui | non
- `garder:Devis:Montant total HT` = oui | non
- `garder:Devis:Taux de TVA` = oui | non
- `garder:Devis:Date de validité` = oui | non
- `garder:Document:Fichier (lien)` = oui | non
- `garder:Document:Mots-clés` = oui | non
- `garder:Document:Description` = oui | non
- `garder:DemandeConge:Date de début` = oui | non
- `garder:DemandeConge:Date de fin` = oui | non
- `garder:DemandeConge:Type de congé` = oui | non
- `garder:DemandeConge:Commentaire` = oui | non
- `garder:CommandeMateriel:Quantité` = oui | non
- `garder:CommandeMateriel:Date de livraison souhaitée` = oui | non
- `garder:CommandeVetement:Article` = oui | non
- `garder:CommandeVetement:Taille` = oui | non
- `garder:CommandeVetement:Quantité` = oui | non
- `garder:CodeAcces:Emplacement du clavier` = oui | non
- `garder:CodeAcces:Date de fin de validité` = oui | non

### Pourquoi chaque droit

- dirigeant / Collaborateur : clôture : affiché dans les Bons d'intervention qu'il voit ; clôture : choisit les Collaborateurs de ses Bons d'intervention — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- dirigeant / Client : tient le registre (supprimer : seulement si le brief le dit) — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- dirigeant / Chantier : tient le registre (supprimer : seulement si le brief le dit) — « adresses des chantiers »
- dirigeant / TypeIntervention : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Checklist personnalisable selon le type d'intervention »
- dirigeant / BonIntervention : tient le registre (supprimer : seulement si le brief le dit) — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- dirigeant / Materiel : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Ajout automatique de matériel avec génération instantanée de devis »
- dirigeant / Devis : tient le registre (supprimer : seulement si le brief le dit) — « génération instantanée de devis »
- dirigeant / CategorieDocument : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « classement des fichiers »
- dirigeant / Document : tient le registre (supprimer : seulement si le brief le dit) — « Gestion documentaire avec classement des fichiers et moteur de recherche »
- dirigeant / CodeAcces : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des codes d'accès digitaux (clavier à code) »
- dirigeant / PointChecklist : enfant de Type d'intervention : même visibilité que le parent, géré par qui gère le parent — « Checklist personnalisable selon le type d'intervention »
- dirigeant / LigneChecklist : enfant de Bon d'intervention : même visibilité que le parent, géré par qui gère le parent — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- dirigeant / LigneMateriel : enfant de Bon d'intervention : même visibilité que le parent, géré par qui gère le parent — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- dirigeant / DemandeConge : décideur du processus : voit tout et fait évoluer l'état — « Gestion intégrée des demandes de congés »
- employe_administratif / Collaborateur : clôture : affiché dans les Bons d'intervention qu'il voit ; clôture : choisit les Collaborateurs de ses Bons d'intervention — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- employe_administratif / Client : tient le registre (supprimer : seulement si le brief le dit) — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- employe_administratif / Chantier : tient le registre (supprimer : seulement si le brief le dit) — « adresses des chantiers »
- employe_administratif / TypeIntervention : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Checklist personnalisable selon le type d'intervention »
- employe_administratif / BonIntervention : tient le registre (supprimer : seulement si le brief le dit) — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- employe_administratif / Materiel : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Ajout automatique de matériel avec génération instantanée de devis »
- employe_administratif / Devis : tient le registre (supprimer : seulement si le brief le dit) — « génération instantanée de devis »
- employe_administratif / CategorieDocument : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « classement des fichiers »
- employe_administratif / Document : tient le registre (supprimer : seulement si le brief le dit) — « Gestion documentaire avec classement des fichiers et moteur de recherche »
- employe_administratif / CodeAcces : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des codes d'accès digitaux (clavier à code) »
- employe_administratif / PointChecklist : enfant de Type d'intervention : même visibilité que le parent, géré par qui gère le parent — « Checklist personnalisable selon le type d'intervention »
- employe_administratif / LigneChecklist : enfant de Bon d'intervention : même visibilité que le parent, géré par qui gère le parent — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- employe_administratif / LigneMateriel : enfant de Bon d'intervention : même visibilité que le parent, géré par qui gère le parent — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- collaborateur / Client : clôture : affiché dans les Bons d'intervention qu'il voit ; clôture : choisit les Clients de ses Bons d'intervention — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- collaborateur / Chantier : clôture : affiché dans les Bons d'intervention qu'il voit ; clôture : choisit les Chantiers de ses Bons d'intervention — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- collaborateur / TypeIntervention : préréglage catalogue : visible de tous les connectés — « Checklist personnalisable selon le type d'intervention »
- collaborateur / PointChecklist : enfant de Type d'intervention : même visibilité que le parent — « Checklist personnalisable selon le type d'intervention »
- collaborateur / Materiel : préréglage catalogue : visible de tous les connectés — « Ajout automatique de matériel avec génération instantanée de devis »
- collaborateur / CategorieDocument : préréglage catalogue : visible de tous les connectés — « classement des fichiers »
- collaborateur / BonIntervention : tient le registre (supprimer : seulement si le brief le dit) — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- collaborateur / Devis : tient le registre (supprimer : seulement si le brief le dit) — « génération instantanée de devis »
- collaborateur / LigneChecklist : enfant de Bon d'intervention : même visibilité que le parent, géré par qui gère le parent — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- collaborateur / LigneMateriel : enfant de Bon d'intervention : même visibilité que le parent, géré par qui gère le parent — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- collaborateur / DemandeConge : préréglage collection + processus : l'initiateur crée et suit les siens — « Gestion intégrée des demandes de congés »
- collaborateur / CommandeMateriel : préréglage collection : le propriétaire crée et modifie les siens — « commandes de matériel »
- collaborateur / CommandeVetement : préréglage collection : le propriétaire crée et modifie les siens — « commandes de matériel et vêtements professionnels »
- collaborateur / Collaborateur : préréglage profil : sa propre fiche, créée automatiquement — « Stockage sécurisé des fiches de paie par collaborateur »

### Refus — blocs : lien:pour-autrui

- [bloc:lien:pour-autrui] FichePaie : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x) [type=value_error, input_value={'app': {'nom': 'c2-porte...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
