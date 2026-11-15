# Gestion POSE — ce que l'usine a compris

En bref : 4 rôles (Le gérant, Le technicien, Le chargé de dépôt, Le client (collectivité)), 19 sortes de fiches, 1 circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- ⚠ Le client (collectivité) ne verra pas les équipements qui le concernent (voir celles qui le désignent : pas encore possible)
- ⚠ Le client (collectivité) ne verra pas les passages prévus qui le concernent (voir celles qui le désignent : pas encore possible)
- ⚠ Le client (collectivité) ne verra pas les rapports de maintenance qui le concernent (voir celles qui le désignent : pas encore possible)
- ⚠ Le client (collectivité) ne verra pas les documents d'équipement qui le concernent (voir celles qui le désignent : pas encore possible)

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Voit tout : activités

## Le gérant (responsable de l'app)
- Voit tout : clients, demandes d'intervention, matériels
- Voit tout, crée et modifie : activités, sites, équipements, chantiers, équipes, affectations, catégories d'intervention, interventions, rapports de maintenance, passages prévus, discussions
- Voit tout, crée, modifie et supprime : documents d'équipement (dans chaque équipement), messages (dans chaque discussion)
- Demandes de devis : voit tout, les fait passer de « rouge » à « orange », les fait passer de « orange » à « vert »

## Le technicien (invité par gerant)
- Voit tout : clients, activités, chantiers, équipes, catégories d'intervention, demandes d'intervention, matériels
- Voit tout, crée et modifie : interventions, rapports de maintenance, discussions
- Voit tout, crée, modifie et supprime : messages (dans chaque discussion)
- Voit seulement les siennes, crée et modifie : bons de commande, réservations de matériel

## Le chargé de dépôt (invité par gerant)
- Voit tout : activités, catégories d'intervention
- Voit tout, crée et modifie : matériels

## Le client (collectivité) (invité par gerant)
- Voit tout : activités, catégories d'intervention
- Voit seulement les siennes, crée et modifie : demandes d'intervention
- Voit seulement les siennes et crée : demandes de devis
- a son client, créé automatiquement, qu'il peut modifier

## Les étapes

- La demande de devis passe par : « rouge » → « orange » → « vert »
  - Le gérant fait passer de « rouge » à « orange »
  - Le gérant fait passer de « orange » à « vert »

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Type de client (collectivité, commune) (choix) · ☐ Adresse (texte long) · ☐ Email de contact (e-mail) · ☐ Téléphone (téléphone) · ☐ Langue préférée (texte court)
- **Activité** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long) · ☐ Photo (lien web)
- **Site** : Nom (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Adresse (texte long) · ☐ Commune (texte court)
- **Équipement** : Type d'équipement (choix parmi : jeux, agrès, panneaux, sols, clôtures) · État (texte court)
  - relié à : site
  - proposé (à cocher) : ☐ Nom ou désignation (texte court) · ☐ Date d'installation (date) · ☐ Fabricant ou référence produit (texte court) · ☐ Valeurs possibles de l'état (choix)
- **Document d'équipement** : Type de document (choix parmi : certificat de conformité, notice de montage, fiche technique, fiche produit, notice d’entretien)
  - relié à : dans chaque équipement
  - proposé (à cocher) : ☐ Fichier du document (lien web) · ☐ Date de validité (date)
- **Chantier** : Nom (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Adresse du chantier (texte long) · ☐ Date de début (date) · ☐ Date de fin (date) · ☐ Description (texte long)
- **Équipe** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Chef d'équipe (texte court)
- **Affectation** : Intitulé (texte court) ◦ choisi par nous
  - relié à : équipe, chantier
  - proposé (à cocher) : ☐ Date de début (date) · ☐ Date de fin (date) · ☐ Consignes (texte long)
- **Catégorie d'intervention** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long)
- **Demande d'intervention** : Objet (texte court) ◦ choisi par nous
  - relié à : catégorie d'intervention
  - proposé (à cocher) : ☐ Description du problème (texte long) · ☐ Urgente (oui / non) · ☐ Photo (lien web)
- **Intervention** : Temps passé (heures) (nombre, facultatif) · Coût (montant, facultatif)
  - relié à : demande d'intervention, équipe, client
  - proposé (à cocher) : ☐ Date de réalisation (date) · ☐ Description des travaux (texte long)
- **Rapport de maintenance** : Type de maintenance (choix parmi : préventive, corrective, urgence)
  - relié à : client, intervention
  - proposé (à cocher) : ☐ Compte rendu (texte long) · ☐ Date du rapport (date) · ☐ Fichier du rapport (lien web)
- **Passage prévu** : Date de passage prévue (date)
  - relié à : client
  - proposé (à cocher) : ☐ Objet du passage (texte court)
- **Demande de devis** : Objet (texte court) ◦ choisi par nous · Réponse (texte long, facultatif)
  - proposé (à cocher) : ☐ Description de la demande (texte long) · ☐ Montant du devis (montant) · ☐ Fichier du devis (lien web)
- **Discussion** : Sujet (texte court) ◦ choisi par nous
  - relié à : chantier, client
- **Message** : Photo HD (lien web, facultatif) · Fichier (lien web, facultatif) · Message vocal (lien web, facultatif)
  - relié à : dans chaque discussion
  - proposé (à cocher) : ☐ Texte du message (texte long) · ☐ Traduction (texte long)
- **Matériel** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Référence (texte court) · ☐ Quantité en stock (nombre)
- **Bon de commande** : Objet (texte court) ◦ choisi par nous
  - relié à : matériel
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Date souhaitée (date) · ☐ Commentaire (texte long)
- **Réservation de matériel** : Objet (texte court) ◦ choisi par nous
  - relié à : matériel
  - proposé (à cocher) : ☐ Date de début (date) · ☐ Date de fin (date) · ☐ Quantité (nombre)

## Questions

- Les visiteurs sans compte pourront consulter toutes les activités — d'accord ? (si certains ne doivent pas être visibles, par exemple des brouillons, répondez non)
- Le technicien verra tous les chantiers, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les discussions qu'il voit; clôture : choisit les chantiers de ses discussions
- Le technicien verra toutes les équipes, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les interventions qu'il voit; clôture : choisit les équipes de ses interventions
- Le technicien verra toutes les interventions, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les rapports de maintenance qu'il voit; clôture : choisit les interventions de ses rapports de maintenance
- Le technicien verra tous les rapports de maintenance, pas seulement ceux qui le concernent — d'accord ?
- Le technicien verra toutes les discussions, pas seulement celles qui le concernent — d'accord ?
- Le technicien verra tous les matériels, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les bons de commande qu'il voit; clôture : choisit les matériels de ses bons de commande
- Le chargé de dépôt verra tous les matériels, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Materiel (registre) : il faut au moins un acteur qui le tient (« manager »)
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : client → « Nom » · activité → « Intitulé » · site → « Nom » · chantier → « Nom » · équipe → « Nom » · affectation → « Intitulé » · catégorie d'intervention → « Nom » · demande d'intervention → « Objet » · demande de devis → « Objet » · discussion → « Sujet » · matériel → « Nom » · bon de commande → « Objet » · réservation de matériel → « Objet »
- « Seulement ceux qui le concernent » n'est pas encore possible : le client (collectivité) doit-il voir TOUS les équipements ?
- « Seulement ceux qui le concernent » n'est pas encore possible : le client (collectivité) doit-il voir TOUS les passages prévus ?
- « Seulement ceux qui le concernent » n'est pas encore possible : le client (collectivité) doit-il voir TOUS les rapports de maintenance ?
- « Seulement ceux qui le concernent » n'est pas encore possible : le client (collectivité) doit-il voir TOUS les documents d'équipement ?
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Site internet vitrine présentant l'activité de l'entreprise — « Créer un site représentatif de l'activité de notre entreprise moderne, épurée, classe ou serait présenté notre activité »
- Application mobile native iOS et Android en plus de l'interface web — « Accès interface web et via application ... accessible via une application mobile (iOS, Android) »
- Suivi des accès individuels (traçabilité de qui se connecte et fait quoi) — « accès individuels avec possibilité de suivi »
- Interface multilingue — « multilingue »
- Consultation des plannings par le client dans son portail — « consulter leurs équipements, plannings et rapports »
- Notifications automatiques au client pour les interventions réalisées — « notifications automatiques pour informer des interventions réalisées »
- Exports des rapports en Excel et PDF — « exportations possibles (Excel, PDF) »
- Planning prévisionnel des passages visible par le client — « Planning prévisionnel de passage »
- Documents joints aux équipements (certificats, notices, fiches techniques) — « listing des équipements avec documentations »
- Tableau de bord global par mois, par équipe et par client — « tableau de bord global (par mois, par équipe, par client) »
- Statistiques et reporting sur le temps passé, les coûts et les interventions — « statistiques et reporting (temps passé, coûts, interventions) »
- Chat intégré type WhatsApp par chantier ou par client — « chat intégré type WhatsApp, par chantier ou par client »
- Notifications liées aux échanges — « notifications et échanges documentés »
- Envoi de photos HD, fichiers et messages vocaux dans les échanges — « photos HD, fichiers, messages vocaux »
- Historique des discussions — « historisation des discussions »
- Traduction vocale — « utilisation de la traduction vocale »
- Réservation de matériel par les techniciens (disponibilité) — « réserver matériels »
- Planning du personnel avec vue par chantier et par équipe — « Organisation du planning du personnel ... vue par chantier/par équipe »
- Gestion des ressources matérielles dans le planning — « gestion des ressources matérielles »
- Paramétrage et filtres personnalisables par l'utilisateur — « paramétrage et filtres personnalisables »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `visiteur:visitor:Activite` = oui | non
- `registre_entier:technicien:Chantier` = oui
- `registre_entier:technicien:Equipe` = oui
- `registre_entier:technicien:Intervention` = oui
- `registre_entier:technicien:RapportMaintenance` = oui | non
- `registre_entier:technicien:Discussion` = oui | non
- `registre_entier:technicien:Materiel` = oui
- `registre_entier:charge_de_depot:Materiel` = oui
- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:Activite:intitule` = oui | <nouveau nom>  (activité → « Intitulé »)
- `nom:Site:nom` = oui | <nouveau nom>  (site → « Nom »)
- `nom:Chantier:nom` = oui | <nouveau nom>  (chantier → « Nom »)
- `nom:Equipe:nom` = oui | <nouveau nom>  (équipe → « Nom »)
- `nom:Affectation:intitule` = oui | <nouveau nom>  (affectation → « Intitulé »)
- `nom:CategorieIntervention:nom` = oui | <nouveau nom>  (catégorie d'intervention → « Nom »)
- `nom:DemandeIntervention:objet` = oui | <nouveau nom>  (demande d'intervention → « Objet »)
- `nom:DemandeDevis:objet` = oui | <nouveau nom>  (demande de devis → « Objet »)
- `nom:Discussion:sujet` = oui | <nouveau nom>  (discussion → « Sujet »)
- `nom:Materiel:nom` = oui | <nouveau nom>  (matériel → « Nom »)
- `nom:BonDeCommande:objet` = oui | <nouveau nom>  (bon de commande → « Objet »)
- `nom:ReservationMateriel:objet` = oui | <nouveau nom>  (réservation de matériel → « Objet »)
- `voir_tous:client:Equipement` = oui | non
- `voir_tous:client:PassagePrevu` = oui | non
- `voir_tous:client:RapportMaintenance` = oui | non
- `voir_tous:client:DocumentEquipement` = oui | non
- `accepter_proposition` = oui | non
- `garder:Client:Type de client (collectivité, commune)` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Client:Email de contact` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Langue préférée` = oui | non
- `garder:Activite:Description` = oui | non
- `garder:Activite:Photo` = oui | non
- `garder:Site:Adresse` = oui | non
- `garder:Site:Commune` = oui | non
- `garder:Equipement:Nom ou désignation` = oui | non
- `garder:Equipement:Date d'installation` = oui | non
- `garder:Equipement:Fabricant ou référence produit` = oui | non
- `garder:Equipement:Valeurs possibles de l'état` = oui | non
- `garder:DocumentEquipement:Fichier du document` = oui | non
- `garder:DocumentEquipement:Date de validité` = oui | non
- `garder:Chantier:Adresse du chantier` = oui | non
- `garder:Chantier:Date de début` = oui | non
- `garder:Chantier:Date de fin` = oui | non
- `garder:Chantier:Description` = oui | non
- `garder:Equipe:Chef d'équipe` = oui | non
- `garder:Affectation:Date de début` = oui | non
- `garder:Affectation:Date de fin` = oui | non
- `garder:Affectation:Consignes` = oui | non
- `garder:CategorieIntervention:Description` = oui | non
- `garder:DemandeIntervention:Description du problème` = oui | non
- `garder:DemandeIntervention:Urgente` = oui | non
- `garder:DemandeIntervention:Photo` = oui | non
- `garder:Intervention:Date de réalisation` = oui | non
- `garder:Intervention:Description des travaux` = oui | non
- `garder:RapportMaintenance:Compte rendu` = oui | non
- `garder:RapportMaintenance:Date du rapport` = oui | non
- `garder:RapportMaintenance:Fichier du rapport` = oui | non
- `garder:PassagePrevu:Objet du passage` = oui | non
- `garder:DemandeDevis:Description de la demande` = oui | non
- `garder:DemandeDevis:Montant du devis` = oui | non
- `garder:DemandeDevis:Fichier du devis` = oui | non
- `garder:Message:Texte du message` = oui | non
- `garder:Message:Traduction` = oui | non
- `garder:Materiel:Référence` = oui | non
- `garder:Materiel:Quantité en stock` = oui | non
- `garder:BonDeCommande:Quantité` = oui | non
- `garder:BonDeCommande:Date souhaitée` = oui | non
- `garder:BonDeCommande:Commentaire` = oui | non
- `garder:ReservationMateriel:Date de début` = oui | non
- `garder:ReservationMateriel:Date de fin` = oui | non
- `garder:ReservationMateriel:Quantité` = oui | non

### Pourquoi chaque droit

- visitor / Activite : catalogue public : visible des visiteurs ; exception : « site internet accessible à tous » — « ou serait présenté notre activité » « site internet accessible à tous »
- gerant / Client : clôture : affiché dans les sites qu'il voit ; clôture : choisit les clients de ses sites — « Gestion des sites »
- gerant / DemandeIntervention : clôture : affiché dans les interventions qu'il voit ; clôture : choisit les demandes d'intervention de ses interventions — « informer des interventions réalisées »
- gerant / Materiel : responsable de l'app : voit les registres de l'équipe (lecture) — « gestion des ressources matérielles »
- gerant / Activite : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « ou serait présenté notre activité »
- gerant / Site : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des sites »
- gerant / Equipement : tient le registre (supprimer : seulement si le brief le dit) — « listing des équipements avec documentations »
- gerant / Chantier : tient le registre (supprimer : seulement si le brief le dit) — « le suivi et la conduite des chantiers »
- gerant / Equipe : tient le registre (supprimer : seulement si le brief le dit) — « affectation des équipes »
- gerant / Affectation : tient le registre (supprimer : seulement si le brief le dit) — « Organisation du planning du personnel »
- gerant / CategorieIntervention : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « classé par catégorie »
- gerant / Intervention : tient le registre (supprimer : seulement si le brief le dit) — « informer des interventions réalisées »
- gerant / RapportMaintenance : tient le registre (supprimer : seulement si le brief le dit) — « bibliothèque de rapports de maintenance (préventive, corrective, urgence) »
- gerant / PassagePrevu : tient le registre (supprimer : seulement si le brief le dit) — « Planning prévisionnel de passage »
- gerant / Discussion : tient le registre (supprimer : seulement si le brief le dit) — « chat intégré type WhatsApp, par chantier ou par client »
- gerant / DocumentEquipement : enfant de équipement : même visibilité que le parent, géré par qui gère le parent — « listing des équipements avec documentations »
- gerant / Message : enfant de discussion : même visibilité que le parent, géré par qui gère le parent — « chat intégré type WhatsApp, par chantier ou par client »
- gerant / DemandeDevis : décideur du processus : voit tout et fait évoluer l'état — « suivi des demandes (rouge, orange, vert) »
- technicien / Client : clôture : affiché dans les interventions qu'il voit ; clôture : choisit les clients de ses interventions — « informer des interventions réalisées »
- technicien / Activite : préréglage catalogue : visible de tous les connectés — « ou serait présenté notre activité »
- technicien / Chantier : clôture : affiché dans les discussions qu'il voit ; clôture : choisit les chantiers de ses discussions — « chat intégré type WhatsApp, par chantier ou par client »
- technicien / Equipe : clôture : affiché dans les interventions qu'il voit ; clôture : choisit les équipes de ses interventions — « informer des interventions réalisées »
- technicien / CategorieIntervention : préréglage catalogue : visible de tous les connectés — « classé par catégorie »
- technicien / DemandeIntervention : clôture : affiché dans les interventions qu'il voit ; clôture : choisit les demandes d'intervention de ses interventions — « informer des interventions réalisées »
- technicien / Materiel : clôture : affiché dans les bons de commande qu'il voit ; clôture : choisit les matériels de ses bons de commande — « possibilité pour nos techniciens d’envoyer des commandes à notre chargé de dépôt »
- technicien / Intervention : tient le registre (supprimer : seulement si le brief le dit) — « informer des interventions réalisées »
- technicien / RapportMaintenance : tient le registre (supprimer : seulement si le brief le dit) — « bibliothèque de rapports de maintenance (préventive, corrective, urgence) »
- technicien / Discussion : tient le registre (supprimer : seulement si le brief le dit) — « chat intégré type WhatsApp, par chantier ou par client »
- technicien / Message : enfant de discussion : même visibilité que le parent, géré par qui gère le parent — « chat intégré type WhatsApp, par chantier ou par client »
- technicien / BonDeCommande : préréglage collection : le propriétaire crée et modifie les siens ; exception : « possibilité pour nos techniciens d’envoyer des commandes à notre chargé de dépôt » — « possibilité pour nos techniciens d’envoyer des commandes à notre chargé de dépôt » « possibilité pour nos techniciens d’envoyer des commandes à notre chargé de dépôt »
- technicien / ReservationMateriel : préréglage collection : le propriétaire crée et modifie les siens ; exception : « possibilité pour nos techniciens » — « et de réserver matériels » « possibilité pour nos techniciens »
- charge_de_depot / Activite : préréglage catalogue : visible de tous les connectés — « ou serait présenté notre activité »
- charge_de_depot / CategorieIntervention : préréglage catalogue : visible de tous les connectés — « classé par catégorie »
- charge_de_depot / Materiel : tient le registre (supprimer : seulement si le brief le dit) — « gestion des ressources matérielles »
- client / Activite : préréglage catalogue : visible de tous les connectés — « ou serait présenté notre activité »
- client / CategorieIntervention : préréglage catalogue : visible de tous les connectés — « classé par catégorie »
- client / DemandeIntervention : préréglage collection : le propriétaire crée et modifie les siens — « Demande d’intervention »
- client / DemandeDevis : préréglage collection + processus : l'initiateur crée et suit les siens ; exception : « suivi des demandes (rouge, orange, vert) » — « suivi des demandes (rouge, orange, vert) » « suivi des demandes (rouge, orange, vert) »
- client / Client : préréglage profil : sa propre fiche, créée automatiquement — « PROFIL PERSONNALISE (soit à nos clients (collectivités, communes) »

### Refus — blocs : portee:designe

- [bloc:portee:designe] client / Equipement : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit)
- [bloc:portee:designe] client / PassagePrevu : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit)
- [bloc:portee:designe] client / RapportMaintenance : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit)
- [bloc:portee:designe] client / DocumentEquipement : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit) [type=value_error, input_value={'app': {'nom': 'c2-clotu...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
