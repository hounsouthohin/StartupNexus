# Interventions techniques — ce que l'usine a compris

En bref : 3 rôles (L'administrateur, Le membre de l'équipe administrative, Le collaborateur), 15 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout : clients, adresses de chantiers, bons d'intervention, types d'intervention, checklists, matériels, lignes de matériel d'intervention (dans chaque bon d'intervention), devis, documents, codes d'accès digitaux
- voit les profils collaborateurs affichés dans les bons d'intervention qu'il consulte (sans page à part)

## Le membre de l'équipe administrative (invité par administrateur)
- Voit tout, crée et modifie : clients, adresses de chantiers, bons d'intervention, types d'intervention, checklists, matériels, devis, documents, codes d'accès digitaux
- Voit tout : profils collaborateurs
- Voit tout, crée, modifie et supprime : lignes de matériel d'intervention (dans chaque bon d'intervention)

## Le collaborateur (invité par administrateur)
- Voit tout : types d'intervention, checklists, matériels, lignes de matériel d'intervention (dans chaque bon d'intervention)
- Voit seulement les siennes, crée et modifie : demandes de congés, commandes de matériel, commandes de vêtements professionnels, fiches de paie
- voit les clients affichés dans les bons d'intervention qu'il consulte (sans page à part)
- a son profil collaborateur, créé automatiquement, qu'il peut modifier
- voit les adresses de chantiers affichées dans les bons d'intervention qu'il consulte (sans page à part)
- Bons d'intervention : voit tout, les fait passer de « début » à « fin »

## Les étapes

- Le bon d'intervention passe par : « début » → « fin »
  - Le collaborateur fait passer de « début » à « fin »

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Profil collaborateur** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Email professionnel (e-mail)
- **Adresse de chantier** : Adresse (texte long)
  - proposé (à cocher) : ☐ Code postal (texte court) · ☐ Ville (texte court)
- **Bon d'intervention** : Horodatage de début (date et heure, facultatif) · Horodatage de fin (date et heure, facultatif) · Signature électronique du client (texte long, facultatif)
  - relié à : client, profil collaborateur, adresse de chantier, type d'intervention
  - proposé (à cocher) : ☐ Compte rendu d’intervention (texte long) · ☐ Observations techniques (texte long)
- **Type d'intervention** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long)
- **Checklist** : Contenu de la checklist (texte long)
  - relié à : type d'intervention
  - proposé (à cocher) : ☐ Nom (texte court)
- **Matériel** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Référence (texte court) · ☐ Prix unitaire (montant)
- **Ligne de matériel d'intervention** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque bon d'intervention, matériel
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Prix unitaire appliqué (montant)
- **Devis** : Intitulé (texte court) ◦ choisi par nous
  - relié à : bon d'intervention, client
  - proposé (à cocher) : ☐ Montant total (montant) · ☐ Date du devis (date)
- **Document** : Classement (texte court)
  - proposé (à cocher) : ☐ Titre du document (texte court) · ☐ Mots-clés (texte court)
- **Demande de congé** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date de début du congé (date) · ☐ Date de fin du congé (date)
- **Commande de matériel** : Intitulé (texte court) ◦ choisi par nous
  - relié à : matériel
  - proposé (à cocher) : ☐ Quantité commandée (nombre) · ☐ Date souhaitée de livraison (date)
- **Commande de vêtement professionnel** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Taille (texte court) · ☐ Quantité (nombre)
- **Fiche de paie** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Mois de paie (date) · ☐ Montant net (montant)
- **Code d'accès digital** : Code d'accès (texte court)
  - proposé (à cocher) : ☐ Description (texte court) · ☐ Date d’expiration (date)

## Questions

- L'administrateur verra les profils collaborateurs (ex. nom, coordonnées) affichés dans les bons d'intervention qu'il traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les bons d'intervention qu'il voit
- Le membre de l'équipe administrative verra tous les clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Client (registre) : il faut au moins un acteur qui le tient (« manager »)
- Le membre de l'équipe administrative verra toutes les adresses de chantiers, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : entité AdresseChantier (registre) : il faut au moins un acteur qui le tient (« manager »)
- Le membre de l'équipe administrative verra tous les bons d'intervention, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité BonIntervention (registre) : il faut au moins un acteur qui le tient (« manager ») ; entité BonIntervention (registre) : l'initiateur (membre_equipe_administrative) doit être parmi ceux qui le tiennent
- Le membre de l'équipe administrative verra tous les devis, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Devis (registre) : il faut au moins un acteur qui le tient (« manager »)
- Le membre de l'équipe administrative verra tous les documents, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Document (registre) : il faut au moins un acteur qui le tient (« manager »)
- Le membre de l'équipe administrative verra tous les codes d'accès digitaux, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité CodeAccesDigital (registre) : il faut au moins un acteur qui le tient (« manager »)
- Le collaborateur verra les clients (ex. nom, coordonnées) affichés dans les bons d'intervention qu'il traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les bons d'intervention qu'il voit
- Le collaborateur verra les adresses de chantiers (ex. nom, coordonnées) affichés dans les bons d'intervention qu'il traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les bons d'intervention qu'il voit
- Le collaborateur verra tous les bons d'intervention, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : voit ce qu'il modifie
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : client → « Nom » · profil collaborateur → « Nom » · type d'intervention → « Nom » · matériel → « Nom » · ligne de matériel d'intervention → « Intitulé » · devis → « Intitulé » · demande de congé → « Intitulé » · commande de matériel → « Intitulé » · commande de vêtement professionnel → « Intitulé » · fiche de paie → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Horodatage précis des interventions — « Horodatage précis des interventions (début et fin) »
- Checklist personnalisable selon le type d'intervention — « Checklist personnalisable selon le type d'intervention »
- Ajout automatique de matériel — « Ajout automatique de matériel »
- Génération instantanée de devis — « génération instantanée de devis »
- Signature électronique du client — « Signature électronique du client sur tablette »
- Gestion documentaire et classement de fichiers — « Gestion documentaire avec classement des fichiers »
- Moteur de recherche documentaire — « moteur de recherche »
- Stockage sécurisé de fiches de paie par collaborateur — « Stockage sécurisé des fiches de paie par collaborateur »
- Gestion des codes d'accès digitaux — « Gestion des codes d'accès digitaux (clavier à code) »
- Documentation technique détaillée — « Documentation technique détaillée »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `vu_via:administrateur:ProfilCollaborateur` = oui
- `registre_entier:membre_equipe_administrative:Client` = oui
- `registre_entier:membre_equipe_administrative:AdresseChantier` = oui
- `registre_entier:membre_equipe_administrative:BonIntervention` = oui
- `registre_entier:membre_equipe_administrative:Devis` = oui
- `registre_entier:membre_equipe_administrative:Document` = oui
- `registre_entier:membre_equipe_administrative:CodeAccesDigital` = oui
- `vu_via:collaborateur:Client` = oui
- `vu_via:collaborateur:AdresseChantier` = oui
- `registre_entier:collaborateur:BonIntervention` = oui
- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:ProfilCollaborateur:nom` = oui | <nouveau nom>  (profil collaborateur → « Nom »)
- `nom:TypeIntervention:nom` = oui | <nouveau nom>  (type d'intervention → « Nom »)
- `nom:Materiel:nom` = oui | <nouveau nom>  (matériel → « Nom »)
- `nom:LigneMaterielIntervention:intitule` = oui | <nouveau nom>  (ligne de matériel d'intervention → « Intitulé »)
- `nom:Devis:intitule` = oui | <nouveau nom>  (devis → « Intitulé »)
- `nom:DemandeConge:intitule` = oui | <nouveau nom>  (demande de congé → « Intitulé »)
- `nom:CommandeMateriel:intitule` = oui | <nouveau nom>  (commande de matériel → « Intitulé »)
- `nom:CommandeVetementProfessionnel:intitule` = oui | <nouveau nom>  (commande de vêtement professionnel → « Intitulé »)
- `nom:FichePaie:intitule` = oui | <nouveau nom>  (fiche de paie → « Intitulé »)
- `garder:Client:Email` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:ProfilCollaborateur:Prénom` = oui | non
- `garder:ProfilCollaborateur:Email professionnel` = oui | non
- `garder:AdresseChantier:Code postal` = oui | non
- `garder:AdresseChantier:Ville` = oui | non
- `garder:BonIntervention:Compte rendu d’intervention` = oui | non
- `garder:BonIntervention:Observations techniques` = oui | non
- `garder:TypeIntervention:Description` = oui | non
- `garder:Checklist:Nom` = oui | non
- `garder:Materiel:Référence` = oui | non
- `garder:Materiel:Prix unitaire` = oui | non
- `garder:LigneMaterielIntervention:Quantité` = oui | non
- `garder:LigneMaterielIntervention:Prix unitaire appliqué` = oui | non
- `garder:Devis:Montant total` = oui | non
- `garder:Devis:Date du devis` = oui | non
- `garder:Document:Titre du document` = oui | non
- `garder:Document:Mots-clés` = oui | non
- `garder:DemandeConge:Date de début du congé` = oui | non
- `garder:DemandeConge:Date de fin du congé` = oui | non
- `garder:CommandeMateriel:Quantité commandée` = oui | non
- `garder:CommandeMateriel:Date souhaitée de livraison` = oui | non
- `garder:CommandeVetementProfessionnel:Taille` = oui | non
- `garder:CommandeVetementProfessionnel:Quantité` = oui | non
- `garder:FichePaie:Mois de paie` = oui | non
- `garder:FichePaie:Montant net` = oui | non
- `garder:CodeAccesDigital:Description` = oui | non
- `garder:CodeAccesDigital:Date d’expiration` = oui | non

### Pourquoi chaque droit

- administrateur / Client : responsable de l'app : voit les registres de l'équipe (lecture) — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- administrateur / AdresseChantier : responsable de l'app : voit les registres de l'équipe (lecture) — « adresses des chantiers »
- administrateur / BonIntervention : responsable de l'app : voit les registres de l'équipe (lecture) — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- administrateur / TypeIntervention : préréglage catalogue : visible de tous les connectés — « type d'intervention »
- administrateur / Checklist : préréglage catalogue : visible de tous les connectés — « Checklist personnalisable selon le type d'intervention »
- administrateur / Materiel : préréglage catalogue : visible de tous les connectés — « Ajout automatique de matériel »
- administrateur / LigneMaterielIntervention : enfant de bon d'intervention : même visibilité que le parent — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- administrateur / Devis : responsable de l'app : voit les registres de l'équipe (lecture) — « génération instantanée de devis »
- administrateur / Document : responsable de l'app : voit les registres de l'équipe (lecture) — « Gestion documentaire avec classement des fichiers et moteur de recherche »
- administrateur / CodeAccesDigital : responsable de l'app : voit les registres de l'équipe (lecture) — « Gestion des codes d'accès digitaux (clavier à code) »
- administrateur / ProfilCollaborateur : clôture : affiché dans les bons d'intervention qu'il voit
- membre_equipe_administrative / Client : tient le registre (supprimer : seulement si le brief le dit) — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- membre_equipe_administrative / AdresseChantier : tient le registre (supprimer : seulement si le brief le dit) — « adresses des chantiers »
- membre_equipe_administrative / BonIntervention : tient le registre (supprimer : seulement si le brief le dit) — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- membre_equipe_administrative / TypeIntervention : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « type d'intervention »
- membre_equipe_administrative / Checklist : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Checklist personnalisable selon le type d'intervention »
- membre_equipe_administrative / Materiel : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Ajout automatique de matériel »
- membre_equipe_administrative / Devis : tient le registre (supprimer : seulement si le brief le dit) — « génération instantanée de devis »
- membre_equipe_administrative / Document : tient le registre (supprimer : seulement si le brief le dit) — « Gestion documentaire avec classement des fichiers et moteur de recherche »
- membre_equipe_administrative / CodeAccesDigital : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des codes d'accès digitaux (clavier à code) »
- membre_equipe_administrative / ProfilCollaborateur : clôture : affiché dans les bons d'intervention qu'il voit ; clôture : choisit les profils collaborateurs de ses bons d'intervention — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- membre_equipe_administrative / LigneMaterielIntervention : enfant de bon d'intervention : même visibilité que le parent, géré par qui gère le parent — « Création et gestion des bons d'intervention (clients, collaborateurs, adresses des chantiers) »
- collaborateur / TypeIntervention : préréglage catalogue : visible de tous les connectés — « type d'intervention »
- collaborateur / Checklist : préréglage catalogue : visible de tous les connectés — « Checklist personnalisable selon le type d'intervention »
- collaborateur / Materiel : préréglage catalogue : visible de tous les connectés — « Ajout automatique de matériel »
- collaborateur / LigneMaterielIntervention : enfant de bon d'intervention : même visibilité que le parent — « Horodatage précis des interventions (début et fin) »
- collaborateur / DemandeConge : préréglage collection : le propriétaire crée et modifie les siens — « demandes de congés »
- collaborateur / CommandeMateriel : préréglage collection : le propriétaire crée et modifie les siens — « commandes de matériel »
- collaborateur / CommandeVetementProfessionnel : préréglage collection : le propriétaire crée et modifie les siens — « commandes de matériel et vêtements professionnels »
- collaborateur / FichePaie : préréglage collection : le propriétaire crée et modifie les siens — « fiches de paie par collaborateur »
- collaborateur / Client : clôture : affiché dans les bons d'intervention qu'il voit
- collaborateur / ProfilCollaborateur : préréglage profil : sa propre fiche, créée automatiquement — « collaborateurs »
- collaborateur / AdresseChantier : clôture : affiché dans les bons d'intervention qu'il voit
- collaborateur / BonIntervention : fait évoluer l'état des fiches du registre — « Horodatage précis des interventions (début et fin) »
