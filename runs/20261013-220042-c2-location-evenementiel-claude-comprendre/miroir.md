# Location événementielle — ce que l'usine a compris

En bref : 2 rôles (Le gérant, Le membre de l'équipe), 12 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant (responsable de l'app)
- Voit tout : membres de l'équipe
- Voit tout, crée et modifie : clients, produits, événements, mouvements de stock, contrats, vidéos, dépenses
- Voit tout, crée, modifie et supprime : lignes de devis (dans chaque devis), affectations de l'équipe (dans chaque événement), instructions de finition (dans chaque événement)
- Devis : voit tout, en crée, les modifie, les fait passer de « en attente » à « confirmé »

## Le membre de l'équipe (invité par gerant)
- Voit tout : clients, produits
- Voit tout, crée et modifie : événements, vidéos
- Voit tout, crée, modifie et supprime : affectations de l'équipe (dans chaque événement), instructions de finition (dans chaque événement)
- a son membre de l'équipe, créé automatiquement, qu'il peut modifier

## Les étapes

- Le devis passe par : « en attente » → « confirmé »
  - Le gérant fait passer de « en attente » à « confirmé »

## Les informations de chaque fiche

- **Membre de l'équipe** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Fonction (ex. montage) (texte court)
- **Client** : Nom (texte court) ◦ choisi par nous · Type de client (choix parmi : particulier, professionnel)
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long) · ☐ Raison sociale (texte court)
- **Produit** : Nom (texte court) ◦ choisi par nous · Valeur (montant) · Mode d'utilisation (texte long)
  - proposé (à cocher) : ☐ Photo (lien web) · ☐ Quantité totale en stock (nombre) · ☐ Catégorie (texte court)
- **Événement** : Date de l'événement (date)
  - relié à : client
  - proposé (à cocher) : ☐ Nom de l'événement (texte court) · ☐ Lieu (texte court) · ☐ Heures de début et de fin (date et heure) · ☐ Type d'événement (texte court)
- **Mouvement de stock** : Sens du mouvement (choix parmi : sortie, entrée)
  - relié à : produit, événement
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Date du mouvement (date)
- **Devis** : Référence (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Date de validité (date) · ☐ Remise (montant)
- **Ligne de devis** : Photo (lien web)
  - relié à : dans chaque devis, produit
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Prix unitaire (montant)
- **Contrat** : Référence (texte court) ◦ choisi par nous
  - relié à : devis, client
  - proposé (à cocher) : ☐ Date de signature (date) · ☐ Montant total (montant) · ☐ Acompte (montant) · ☐ Document signé (lien web)
- **Affectation de l'équipe** : Rôle (texte court) ◦ choisi par nous
  - relié à : dans chaque événement, membre de l'équipe
  - proposé (à cocher) : ☐ Heure d'arrivée (date et heure)
- **Instruction de finition** : Instructions de finition (texte long)
  - relié à : dans chaque événement
  - proposé (à cocher) : ☐ Titre (texte court) · ☐ Ordre (nombre)
- **Vidéo** : Type de vidéo (choix parmi : test, installation, finition) · Lien de la vidéo (lien web)
  - relié à : événement, produit
  - proposé (à cocher) : ☐ Commentaire (texte long)
- **Dépense** : Montant (montant)
  - relié à : événement
  - proposé (à cocher) : ☐ Libellé (texte court) · ☐ Date de la dépense (date) · ☐ Catégorie (texte court)

## Questions

- Le membre de l'équipe verra tous les clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les événements qu'il voit; clôture : choisit les clients de ses événements
- Le membre de l'équipe verra tous les événements, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les vidéos qu'il voit; clôture : choisit les événements de ses vidéos
- Le membre de l'équipe verra toutes les vidéos, pas seulement celles qui le concernent — d'accord ?
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : membre de l'équipe → « Nom » · client → « Nom » · produit → « Nom » · devis → « Référence » · contrat → « Référence » · affectation de l'équipe → « Rôle »

## Pas encore dans notre stock (vos mots)

- Suivi des quantités en stock selon les sorties et entrées de matériel liées aux événements — « Gestion des stocks en fonction des événements au calendrier (sorties et entrées) »
- Photo pour chaque élément du devis — « Chaque élément dans le devis doit avoir une photo pour représenter l'effet »
- Rappel à l'équipe de montage du bon mode d'utilisation de chaque appareil et des consignes de finition (s'il s'agit de rappels envoyés et pas seulement de fiches de consignes, à confirmer avec le client) — « Développer une méthode pour rappeler le mode d'utilisation correct de chaque appareil »
- Vidéos de test, d'installation et de finition du matériel, à déposer obligatoirement par l'équipe — « Exiger que l'équipe réalise des vidéos de test du matériel, ainsi que des vidéos d'installation et de finition du matériel »
- Calcul du profit final de chaque événement à partir des dépenses — « Gestion des dépenses pour chaque événement et visualisation du profit final »
- Rapports mensuels et par événement, avec filtres — « Système de filtrage et visualisation simple des rapports mensuels et par événement »
- Vue calendrier des événements, dans le style de Google Agenda — « Calendrier dans le style de Google »
- Synchronisation des données avec le calendrier Apple Calendar déjà utilisé — « intégration de données avec notre calendrier actuel sur Apple Calendar »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:membre_equipe:Client` = oui
- `registre_entier:membre_equipe:Evenement` = oui
- `registre_entier:membre_equipe:Video` = oui | non
- `nom:MembreEquipe:nom` = oui | <nouveau nom>  (membre de l'équipe → « Nom »)
- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:Produit:nom` = oui | <nouveau nom>  (produit → « Nom »)
- `nom:Devis:reference` = oui | <nouveau nom>  (devis → « Référence »)
- `nom:Contrat:reference` = oui | <nouveau nom>  (contrat → « Référence »)
- `nom:Affectation:role` = oui | <nouveau nom>  (affectation de l'équipe → « Rôle »)
- `garder:MembreEquipe:Téléphone` = oui | non
- `garder:MembreEquipe:Fonction (ex. montage)` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Client:Raison sociale` = oui | non
- `garder:Produit:Photo` = oui | non
- `garder:Produit:Quantité totale en stock` = oui | non
- `garder:Produit:Catégorie` = oui | non
- `garder:Evenement:Nom de l'événement` = oui | non
- `garder:Evenement:Lieu` = oui | non
- `garder:Evenement:Heures de début et de fin` = oui | non
- `garder:Evenement:Type d'événement` = oui | non
- `garder:MouvementStock:Quantité` = oui | non
- `garder:MouvementStock:Date du mouvement` = oui | non
- `garder:Devis:Date de validité` = oui | non
- `garder:Devis:Remise` = oui | non
- `garder:LigneDevis:Quantité` = oui | non
- `garder:LigneDevis:Prix unitaire` = oui | non
- `garder:Contrat:Date de signature` = oui | non
- `garder:Contrat:Montant total` = oui | non
- `garder:Contrat:Acompte` = oui | non
- `garder:Contrat:Document signé` = oui | non
- `garder:Affectation:Heure d'arrivée` = oui | non
- `garder:InstructionFinition:Titre` = oui | non
- `garder:InstructionFinition:Ordre` = oui | non
- `garder:Video:Commentaire` = oui | non
- `garder:Depense:Libellé` = oui | non
- `garder:Depense:Date de la dépense` = oui | non
- `garder:Depense:Catégorie` = oui | non

### Pourquoi chaque droit

- gerant / MembreEquipe : clôture : affiché dans les affectations de l'équipe qu'il voit ; clôture : choisit les membres de l'équipe de ses affectations de l'équipe — « Gestion de l'équipe pour chaque événement »
- gerant / Client : tient le registre (supprimer : seulement si le brief le dit) — « Nous avons besoin d'un CRM pour les données des clients »
- gerant / Produit : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « rappeler le mode d'utilisation correct de chaque appareil »
- gerant / Evenement : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des stocks en fonction des événements au calendrier »
- gerant / MouvementStock : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des stocks en fonction des événements au calendrier (sorties et entrées) »
- gerant / Contrat : tient le registre (supprimer : seulement si le brief le dit) — « après confirmation, gestion des contrats »
- gerant / Video : tient le registre (supprimer : seulement si le brief le dit) — « Exiger que l'équipe réalise des vidéos de test du matériel, ainsi que des vidéos d'installation et de finition du matériel »
- gerant / Depense : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des dépenses pour chaque événement et visualisation du profit final »
- gerant / LigneDevis : enfant de devis : même visibilité que le parent, géré par qui gère le parent — « Gestion des devis pour chaque client » « Gestion des devis pour chaque client ; après confirmation, gestion des contrats »
- gerant / Affectation : enfant de événement : même visibilité que le parent, géré par qui gère le parent — « Gestion des stocks en fonction des événements au calendrier »
- gerant / InstructionFinition : enfant de événement : même visibilité que le parent, géré par qui gère le parent — « Gestion des stocks en fonction des événements au calendrier »
- gerant / Devis : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre — « Gestion des devis pour chaque client » « Gestion des devis pour chaque client ; après confirmation, gestion des contrats »
- membre_equipe / Client : clôture : affiché dans les événements qu'il voit ; clôture : choisit les clients de ses événements — « Gestion des stocks en fonction des événements au calendrier »
- membre_equipe / Produit : préréglage catalogue : visible de tous les connectés — « rappeler le mode d'utilisation correct de chaque appareil »
- membre_equipe / Evenement : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des stocks en fonction des événements au calendrier »
- membre_equipe / Video : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Exiger que l'équipe réalise des vidéos de test du matériel » — « Exiger que l'équipe réalise des vidéos de test du matériel, ainsi que des vidéos d'installation et de finition du matériel » « Exiger que l'équipe réalise des vidéos de test du matériel »
- membre_equipe / Affectation : enfant de événement : même visibilité que le parent, géré par qui gère le parent — « Gestion des stocks en fonction des événements au calendrier »
- membre_equipe / InstructionFinition : exception : « des instructions pour les finitions lors de l'événement, destinées à l'équipe de montage » ; enfant de événement : même visibilité que le parent, géré par qui gère le parent — « des instructions pour les finitions lors de l'événement, destinées à l'équipe de montage » « Gestion des stocks en fonction des événements au calendrier »
- membre_equipe / MembreEquipe : préréglage profil : sa propre fiche, créée automatiquement — « toute l'équipe qui y travaillera »
