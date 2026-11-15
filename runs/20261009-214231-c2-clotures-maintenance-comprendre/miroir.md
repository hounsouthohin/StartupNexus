# Gestion POSE — ce que l'usine a compris

En bref : 3 rôles (L'administrateur pose, Le personnel de l'entreprise, La collectivité cliente), 22 sortes de fiches, 1 circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- ⚠ La collectivité cliente ne verra pas les équipements qui le concernent (voir celles qui le désignent : pas encore possible)
- ⚠ La collectivité cliente ne verra pas les passages planifiés qui le concernent (voir celles qui le désignent : pas encore possible)
- ⚠ La collectivité cliente ne verra pas les rapports de maintenance qui le concernent (voir celles qui le désignent : pas encore possible)
- ⚠ La collectivité cliente ne verra pas les documents d'équipement qui le concernent (voir celles qui le désignent : pas encore possible)
- choisir, dans un(e) demande d'intervention, un(e) site client parmi les siens : pas encore possible — lien retiré
- choisir, dans un(e) demande d'intervention, un(e) équipement parmi les siens : pas encore possible — lien retiré
- choisir, dans un(e) demande de devis, un(e) site client parmi les siens : pas encore possible — lien retiré
- choisir, dans un(e) demande de devis, un(e) équipement parmi les siens : pas encore possible — lien retiré

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Voit tout : pages du site internet

## L'administrateur pose (responsable de l'app)
- Voit tout, crée et modifie : pages du site internet, sites clients, équipements, catégories de demande d'intervention, interventions, devis, rapports de maintenance, passages planifiés, chantiers, équipes, créneaux de planning du personnel, conversations, matériels, bons de commande internes
- Voit tout : profils personnel de l'entreprise, profils collectivité cliente, demandes d'intervention, demandes de devis
- Voit tout, crée, modifie et supprime : documents d'équipement (dans chaque équipement), messages de conversation (dans chaque conversation)
- a son profil administrateur POSE, créé automatiquement, qu'il peut modifier

## Le personnel de l'entreprise (invité par administrateur_pose)
- Voit tout : pages du site internet, profils collectivité cliente, catégories de demande d'intervention, demandes d'intervention
- Voit tout, crée et modifie : sites clients, équipements, interventions, devis, rapports de maintenance, passages planifiés, chantiers, équipes, créneaux de planning du personnel, conversations, matériels, bons de commande internes
- Voit tout, crée, modifie et supprime : documents d'équipement (dans chaque équipement), messages de conversation (dans chaque conversation)
- Voit seulement les siennes, crée et modifie : réservations de matériel
- a son profil personnel de l'entreprise, créé automatiquement, qu'il peut modifier
- Demandes de devis : voit tout, les fait passer de « orange » à « vert »

## La collectivité cliente (invité par administrateur_pose)
- Voit tout : pages du site internet, catégories de demande d'intervention, rapports de maintenance
- Voit seulement les siennes, crée et modifie : demandes d'intervention
- a son profil collectivité cliente, créé automatiquement, qu'il peut modifier
- voit les sites clients affichés dans les rapports de maintenance qu'il consulte (sans page à part)
- voit les équipements affichés dans les rapports de maintenance qu'il consulte (sans page à part)
- voit les interventions affichées dans les rapports de maintenance qu'il consulte (sans page à part)
- Demandes de devis : voit seulement les siennes, en crée, les fait passer de « rouge » à « orange »

## Les étapes

- La demande de devis passe par : « rouge » → « orange » → « vert »
  - Le personnel de l'entreprise fait passer de « orange » à « vert »
  - La collectivité cliente fait passer de « rouge » à « orange »

## Les informations de chaque fiche

- **Page du site internet** : Titre (texte court) ◦ choisi par nous
- **Profil administrateur pose** : Nom (texte court) ◦ choisi par nous
- **Profil personnel de l'entreprise** : Nom (texte court) ◦ choisi par nous
- **Profil collectivité cliente** : Nom de la collectivité (texte court) ◦ choisi par nous
- **Site client** : Nom (texte court) ◦ choisi par nous
  - relié à : profil collectivité cliente
- **Équipement** : Type d’équipement (choix parmi : jeux, agrès, panneaux, sols, clôtures) · État (texte court)
  - relié à : site client, profil collectivité cliente
- **Document d'équipement** : Type de document (choix parmi : certificat de conformité, notice de montage, fiche technique, fiche produit, notice d’entretien)
  - relié à : dans chaque équipement
  - proposé (à cocher) : ☐ Fichier du document (lien web)
- **Catégorie de demande d'intervention** : Libellé (texte court) ◦ choisi par nous
- **Demande d'intervention** : Intitulé (texte court) ◦ choisi par nous
  - relié à : profil collectivité cliente, catégorie de demande d'intervention
- **Intervention** : Urgence (oui / non) · Temps passé (nombre) · Coût (montant)
  - relié à : demande d'intervention, site client, équipement, équipe
- **Demande de devis** : Intitulé (texte court) ◦ choisi par nous
  - relié à : profil collectivité cliente
- **Devis** : Réponse (texte long)
  - relié à : demande de devis, profil collectivité cliente
- **Rapport de maintenance** : Type de maintenance (choix parmi : préventive, corrective, urgence)
  - relié à : intervention, site client, équipement, profil collectivité cliente
- **Passage planifié** : Date et heure de passage (date et heure)
  - relié à : site client, équipement, intervention, équipe
- **Chantier** : Nom (texte court) ◦ choisi par nous
  - relié à : profil collectivité cliente, site client
- **Équipe** : Nom (texte court) ◦ choisi par nous
  - relié à : profil personnel de l'entreprise
- **Créneau de planning du personnel** : Libellé (texte court) ◦ choisi par nous
  - relié à : chantier, équipe
- **Conversation** : Titre (texte court) ◦ choisi par nous
  - relié à : chantier, profil collectivité cliente
- **Message de conversation** : Photo HD (lien web, facultatif) · Fichier (lien web, facultatif) · Message vocal (lien web, facultatif)
  - relié à : dans chaque conversation, profil personnel de l'entreprise, profil collectivité cliente
- **Matériel** : Nom (texte court) ◦ choisi par nous
- **Bon de commande interne** : Référence (texte court) ◦ choisi par nous
  - relié à : matériel, profil personnel de l'entreprise
- **Réservation de matériel** : Référence (texte court) ◦ choisi par nous
  - relié à : matériel, chantier

## Questions

- Les visiteurs sans compte pourront consulter toutes les pages du site internet — d'accord ? (si certains ne doivent pas être visibles, par exemple des brouillons, répondez non)
- Le personnel de l'entreprise verra toutes les pages du site internet, pas seulement celles qui le concernent — d'accord ?
- Le personnel de l'entreprise verra tous les sites clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les équipements qu'il voit; clôture : choisit les sites clients de ses équipements
- Le personnel de l'entreprise verra tous les équipements, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les interventions qu'il voit; clôture : choisit les équipements de ses interventions
- Le personnel de l'entreprise verra toutes les interventions, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les rapports de maintenance qu'il voit; clôture : choisit les interventions de ses rapports de maintenance
- Le personnel de l'entreprise verra tous les devis, pas seulement ceux qui le concernent — d'accord ?
- Le personnel de l'entreprise verra tous les rapports de maintenance, pas seulement ceux qui le concernent — d'accord ?
- Le personnel de l'entreprise verra tous les passages planifiés, pas seulement ceux qui le concernent — d'accord ?
- Le personnel de l'entreprise verra tous les chantiers, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les créneaux de planning du personnel qu'il voit; clôture : choisit les chantiers de ses créneaux de planning du personnel
- Le personnel de l'entreprise verra toutes les équipes, pas seulement celles qui le concernent — d'accord ?
- Le personnel de l'entreprise verra tous les créneaux de planning du personnel, pas seulement ceux qui le concernent — d'accord ?
- Le personnel de l'entreprise verra toutes les conversations, pas seulement celles qui le concernent — d'accord ?
- Le personnel de l'entreprise verra tous les matériels, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les bons de commande internes qu'il voit; clôture : choisit les matériels de ses bons de commande internes
- Le personnel de l'entreprise verra tous les bons de commande internes, pas seulement ceux qui le concernent — d'accord ?
- La collectivité cliente verra toutes les pages du site internet, pas seulement celles qui la concernent — d'accord ?
- La collectivité cliente verra les sites clients (ex. nom, coordonnées) affichés dans les rapports de maintenance qu'elle traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les rapports de maintenance qu'il voit
- La collectivité cliente verra les équipements (ex. nom, coordonnées) affichés dans les rapports de maintenance qu'elle traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les rapports de maintenance qu'il voit
- La collectivité cliente verra les interventions (ex. nom, coordonnées) affichés dans les rapports de maintenance qu'elle traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les rapports de maintenance qu'il voit
- La collectivité cliente verra tous les rapports de maintenance, pas seulement ceux qui la concernent — d'accord ?
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : page du site internet → « Titre » · profil administrateur POSE → « Nom » · profil personnel de l'entreprise → « Nom » · profil collectivité cliente → « Nom de la collectivité » · site client → « Nom » · catégorie de demande d'intervention → « Libellé » · demande d'intervention → « Intitulé » · demande de devis → « Intitulé » · chantier → « Nom » · équipe → « Nom » · créneau de planning du personnel → « Libellé » · conversation → « Titre » · matériel → « Nom » · bon de commande interne → « Référence » · réservation de matériel → « Référence »
- « Seulement ceux qui le concernent » n'est pas encore possible : la collectivité cliente doit-elle voir TOUS les équipements ? → **non, nécessairement** : Collectivité cliente crée des demandes d'intervention qui désignent des sites clients, mais ne voit pas les siens : les lui montrer tous exposerait ceux des autres — « celles qui le désignent » arrive en N1.3 ; Collectivité cliente crée des demandes de devis qui désignent des sites clients, mais ne voit pas les siens : les lui montrer tous exposerait ceux des autres — « celles qui le désignent » a
- « Seulement ceux qui le concernent » n'est pas encore possible : la collectivité cliente doit-elle voir TOUS les passages planifiés ?
- « Seulement ceux qui le concernent » n'est pas encore possible : la collectivité cliente doit-elle voir TOUS les rapports de maintenance ?
- « Seulement ceux qui le concernent » n'est pas encore possible : la collectivité cliente doit-elle voir TOUS les documents d'équipement ?
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Site internet vitrine de présentation de l’entreprise — « Créer un site représentatif de l'activité de notre entreprise moderne, épurée, classe ou serait présenté notre activité »
- Application mobile iOS/Android — « accessible via une application mobile (iOS, Android) »
- Suivi ou traçabilité des accès individuels — « accès sécurisé(accès individuels avec possibilité de suivi) »
- Interface multilingue — « multilingue »
- Ajout de modules / modularité du produit — « possibilité d’ajout de modules »
- Consultation et gestion de plannings — « consulter leurs équipements, plannings et rapports – suivi du patrimoine/équipements/sols ... Planning prévisionnel de passage ... Organisation du planning du personnel »
- Notifications automatiques aux clients — « notifications automatiques pour informer des interventions réalisées. »
- Bibliothèque de rapports de maintenance — « accès à la bibliothèque de rapports de maintenance (préventive, corrective, urgence) »
- Export Excel et PDF — « exportations possibles (Excel, PDF) »
- Documentations et pièces jointes liées aux équipements — « listing des équipements avec documentations (certificat de conformité, notice de montage, fiche technique, fiche produit, notice d’entretien) »
- Affectation des équipes aux interventions — « affectation des équipes. »
- Tableau de bord global — « tableau de bord global (par mois, par équipe, par client) »
- Statistiques et reporting sur temps, coûts et interventions — « statistiques et reporting (temps passé, coûts, interventions) »
- Chat intégré par chantier ou par client — « chat intégré type WhatsApp, par chantier ou par client »
- Notifications liées à la communication — « notifications et échanges documentés (photos HD, fichiers, messages vocaux) »
- Photos HD, fichiers et messages vocaux dans les échanges — « photos HD, fichiers, messages vocaux »
- Historisation des discussions — « historisation des discussions »
- Traduction vocale — « utilisation de la traduction vocale. »
- Réservation de matériel — « réserver matériels »
- Gestion des ressources matérielles — « gestion des ressources matérielles »
- Paramétrage et filtres personnalisables — « paramétrage et filtres personnalisables »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `visiteur:visitor:PageSiteInternet` = oui | non
- `registre_entier:personnel_entreprise:PageSiteInternet` = oui | non
- `registre_entier:personnel_entreprise:SiteClient` = oui
- `registre_entier:personnel_entreprise:Equipement` = oui
- `registre_entier:personnel_entreprise:Intervention` = oui
- `registre_entier:personnel_entreprise:Devis` = oui | non
- `registre_entier:personnel_entreprise:RapportMaintenance` = oui | non
- `registre_entier:personnel_entreprise:PassagePlanifie` = oui | non
- `registre_entier:personnel_entreprise:Chantier` = oui
- `registre_entier:personnel_entreprise:Equipe` = oui | non
- `registre_entier:personnel_entreprise:CreneauPlanningPersonnel` = oui | non
- `registre_entier:personnel_entreprise:Conversation` = oui | non
- `registre_entier:personnel_entreprise:Materiel` = oui
- `registre_entier:personnel_entreprise:BonCommandeInterne` = oui | non
- `registre_entier:client_collectivite:PageSiteInternet` = oui | non
- `vu_via:client_collectivite:SiteClient` = oui
- `vu_via:client_collectivite:Equipement` = oui
- `vu_via:client_collectivite:Intervention` = oui
- `registre_entier:client_collectivite:RapportMaintenance` = oui | non
- `nom:PageSiteInternet:titre` = oui | <nouveau nom>  (page du site internet → « Titre »)
- `nom:ProfilAdministrateurPose:nom` = oui | <nouveau nom>  (profil administrateur POSE → « Nom »)
- `nom:ProfilPersonnelEntreprise:nom` = oui | <nouveau nom>  (profil personnel de l'entreprise → « Nom »)
- `nom:ProfilCollectiviteCliente:nomCollectivite` = oui | <nouveau nom>  (profil collectivité cliente → « Nom de la collectivité »)
- `nom:SiteClient:nom` = oui | <nouveau nom>  (site client → « Nom »)
- `nom:CategorieDemandeIntervention:libelle` = oui | <nouveau nom>  (catégorie de demande d'intervention → « Libellé »)
- `nom:DemandeIntervention:intitule` = oui | <nouveau nom>  (demande d'intervention → « Intitulé »)
- `nom:DemandeDevis:intitule` = oui | <nouveau nom>  (demande de devis → « Intitulé »)
- `nom:Chantier:nom` = oui | <nouveau nom>  (chantier → « Nom »)
- `nom:Equipe:nom` = oui | <nouveau nom>  (équipe → « Nom »)
- `nom:CreneauPlanningPersonnel:libelle` = oui | <nouveau nom>  (créneau de planning du personnel → « Libellé »)
- `nom:Conversation:titre` = oui | <nouveau nom>  (conversation → « Titre »)
- `nom:Materiel:nom` = oui | <nouveau nom>  (matériel → « Nom »)
- `nom:BonCommandeInterne:reference` = oui | <nouveau nom>  (bon de commande interne → « Référence »)
- `nom:ReservationMateriel:reference` = oui | <nouveau nom>  (réservation de matériel → « Référence »)
- `voir_tous:client_collectivite:Equipement` = non
- `voir_tous:client_collectivite:PassagePlanifie` = oui | non
- `voir_tous:client_collectivite:RapportMaintenance` = oui | non
- `voir_tous:client_collectivite:DocumentEquipement` = oui | non
- `accepter_proposition` = oui | non
- `garder:DocumentEquipement:Fichier du document` = oui | non

### Pourquoi chaque droit

- visitor / PageSiteInternet : registre public : visible de tous ; exception : « site internet accessible à tous » — « site internet accessible à tous » « site internet accessible à tous »
- administrateur_pose / PageSiteInternet : tient le registre (supprimer : seulement si le brief le dit) — « site internet accessible à tous »
- administrateur_pose / SiteClient : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des sites »
- administrateur_pose / Equipement : tient le registre (supprimer : seulement si le brief le dit) — « listing des équipements avec documentations (certificat de conformité, notice de montage, fiche technique, fiche produit, notice d’entretien) »
- administrateur_pose / CategorieDemandeIntervention : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « classé par catégorie »
- administrateur_pose / Intervention : tient le registre (supprimer : seulement si le brief le dit) — « gestion des interventions d’urgence »
- administrateur_pose / Devis : tient le registre (supprimer : seulement si le brief le dit) — « réponses aux demandes de devis »
- administrateur_pose / RapportMaintenance : tient le registre (supprimer : seulement si le brief le dit) — « bibliothèque de rapports de maintenance (préventive, corrective, urgence) »
- administrateur_pose / PassagePlanifie : tient le registre (supprimer : seulement si le brief le dit) — « Planning prévisionnel de passage »
- administrateur_pose / Chantier : tient le registre (supprimer : seulement si le brief le dit) — « suivi et la conduite des chantiers »
- administrateur_pose / Equipe : tient le registre (supprimer : seulement si le brief le dit) — « affectation des équipes »
- administrateur_pose / CreneauPlanningPersonnel : tient le registre (supprimer : seulement si le brief le dit) — « vue par chantier/par équipe »
- administrateur_pose / Conversation : tient le registre (supprimer : seulement si le brief le dit) — « chat intégré type WhatsApp, par chantier ou par client »
- administrateur_pose / Materiel : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des commandes/matériels »
- administrateur_pose / BonCommandeInterne : tient le registre (supprimer : seulement si le brief le dit) — « bon de commande internes (possibilité pour nos techniciens d’envoyer des commandes »
- administrateur_pose / ProfilPersonnelEntreprise : clôture : affiché dans les équipes qu'il voit ; clôture : choisit les profils personnel de l'entreprise de ses équipes — « affectation des équipes »
- administrateur_pose / ProfilCollectiviteCliente : clôture : affiché dans les sites clients qu'il voit ; clôture : choisit les profils collectivité cliente de ses sites clients — « Gestion des sites »
- administrateur_pose / DemandeIntervention : clôture : affiché dans les interventions qu'il voit ; clôture : choisit les demandes d'intervention de ses interventions — « gestion des interventions d’urgence »
- administrateur_pose / DemandeDevis : clôture : affiché dans les devis qu'il voit ; clôture : choisit les demandes de devis de ses devis — « réponses aux demandes de devis »
- administrateur_pose / DocumentEquipement : enfant de équipement : même visibilité que le parent, géré par qui gère le parent — « listing des équipements avec documentations (certificat de conformité, notice de montage, fiche technique, fiche produit, notice d’entretien) »
- administrateur_pose / MessageConversation : enfant de conversation : même visibilité que le parent, géré par qui gère le parent — « chat intégré type WhatsApp, par chantier ou par client »
- administrateur_pose / ProfilAdministrateurPose : préréglage profil : sa propre fiche, créée automatiquement — « accès sécurisé(accès individuels avec possibilité de suivi) »
- personnel_entreprise / PageSiteInternet : registre public : visible de tous — « site internet accessible à tous »
- personnel_entreprise / ProfilCollectiviteCliente : clôture : affiché dans les sites clients qu'il voit ; clôture : choisit les profils collectivité cliente de ses sites clients — « Gestion des sites »
- personnel_entreprise / CategorieDemandeIntervention : préréglage catalogue : visible de tous les connectés — « classé par catégorie »
- personnel_entreprise / DemandeIntervention : clôture : affiché dans les interventions qu'il voit ; clôture : choisit les demandes d'intervention de ses interventions — « gestion des interventions d’urgence »
- personnel_entreprise / SiteClient : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des sites »
- personnel_entreprise / Equipement : tient le registre (supprimer : seulement si le brief le dit) ; exception : « INTERFACE ENTREPRISE

Gestion des sites:

- listing des équipements » — « listing des équipements avec documentations (certificat de conformité, notice de montage, fiche technique, fiche produit, notice d’entretien) » « INTERFACE ENTREPRISE

Gestion des sites:

- listing des équipements »
- personnel_entreprise / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; exception : « INTERFACE ENTREPRISE

Gestion des sites:

- listing des équipements avec documentations (certificat de conformité, notice de montage, fiche technique, fiche produit, notice d’entretien) ;

Demande d’intervention:

- gestion des interventions d’urgence ;

- affectation des équipes » — « gestion des interventions d’urgence » « INTERFACE ENTREPRISE

Gestion des sites:

- listing des équipements avec documentations (certificat de conformité, notice de montage, fiche technique, fiche produit, notice d’entretien) ;

Demande d’intervention:

- gestion des interventions d’urgence ;

- affectation des équipes »
- personnel_entreprise / Devis : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Demande de devis:

- réponses aux demandes de devis » — « réponses aux demandes de devis » « Demande de devis:

- réponses aux demandes de devis »
- personnel_entreprise / RapportMaintenance : tient le registre (supprimer : seulement si le brief le dit) — « bibliothèque de rapports de maintenance (préventive, corrective, urgence) »
- personnel_entreprise / PassagePlanifie : tient le registre (supprimer : seulement si le brief le dit) — « Planning prévisionnel de passage »
- personnel_entreprise / Chantier : tient le registre (supprimer : seulement si le brief le dit) — « suivi et la conduite des chantiers »
- personnel_entreprise / Equipe : tient le registre (supprimer : seulement si le brief le dit) — « affectation des équipes »
- personnel_entreprise / CreneauPlanningPersonnel : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Organisation du planning du personnel:

- vue par chantier/par équipe » — « vue par chantier/par équipe » « Organisation du planning du personnel:

- vue par chantier/par équipe »
- personnel_entreprise / Conversation : tient le registre (supprimer : seulement si le brief le dit) — « chat intégré type WhatsApp, par chantier ou par client »
- personnel_entreprise / Materiel : tient le registre (supprimer : seulement si le brief le dit) ; exception : « gestion des ressources matérielles » — « Gestion des commandes/matériels » « gestion des ressources matérielles »
- personnel_entreprise / BonCommandeInterne : tient le registre (supprimer : seulement si le brief le dit) ; exception : « possibilité pour nos techniciens d’envoyer des commandes à notre chargé de dépôt » — « bon de commande internes (possibilité pour nos techniciens d’envoyer des commandes » « possibilité pour nos techniciens d’envoyer des commandes à notre chargé de dépôt »
- personnel_entreprise / DocumentEquipement : exception : « INTERFACE ENTREPRISE

Gestion des sites:

- listing des équipements avec documentations » ; enfant de équipement : même visibilité que le parent, géré par qui gère le parent — « INTERFACE ENTREPRISE

Gestion des sites:

- listing des équipements avec documentations » « listing des équipements avec documentations (certificat de conformité, notice de montage, fiche technique, fiche produit, notice d’entretien) » « INTERFACE ENTREPRISE

Gestion des sites:

- listing des équipements »
- personnel_entreprise / MessageConversation : enfant de conversation : même visibilité que le parent, géré par qui gère le parent — « chat intégré type WhatsApp, par chantier ou par client »
- personnel_entreprise / ReservationMateriel : préréglage collection : le propriétaire crée et modifie les siens ; exception : « possibilité pour nos techniciens d’envoyer des commandes à notre chargé de dépôt et de réserver matériels » — « réserver matériels » « possibilité pour nos techniciens d’envoyer des commandes à notre chargé de dépôt et de réserver matériels »
- personnel_entreprise / ProfilPersonnelEntreprise : préréglage profil : sa propre fiche, créée automatiquement — « personnels de notre entreprise »
- personnel_entreprise / DemandeDevis : décideur du processus : voit tout et fait évoluer l'état — « Demande de devis:

- suivi des demandes (rouge, orange, vert) »
- client_collectivite / PageSiteInternet : registre public : visible de tous — « site internet accessible à tous »
- client_collectivite / CategorieDemandeIntervention : préréglage catalogue : visible de tous les connectés — « classé par catégorie »
- client_collectivite / RapportMaintenance : exception : « accès à la bibliothèque de rapports de maintenance » — « accès à la bibliothèque de rapports de maintenance »
- client_collectivite / DemandeIntervention : préréglage collection : le propriétaire crée et modifie les siens — « Demande d’intervention:

-classé par catégorie »
- client_collectivite / ProfilCollectiviteCliente : préréglage profil : sa propre fiche, créée automatiquement — « nos clients (collectivités, communes) »
- client_collectivite / SiteClient : clôture : affiché dans les rapports de maintenance qu'il voit
- client_collectivite / Equipement : clôture : affiché dans les rapports de maintenance qu'il voit
- client_collectivite / Intervention : clôture : affiché dans les rapports de maintenance qu'il voit
- client_collectivite / DemandeDevis : préréglage collection + processus : l'initiateur crée et suit les siens ; fait l'étape depuis « rouge » ; exception : « suivi des demandes (rouge, orange, vert) » — « suivi des demandes (rouge, orange, vert) » « Demande de devis:

- suivi des demandes (rouge, orange, vert) » « suivi des demandes (rouge, orange, vert) »

### Refus — blocs : portee:designe

- [bloc:portee:designe] client_collectivite / Equipement : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit)
- [bloc:portee:designe] client_collectivite / PassagePlanifie : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit)
- [bloc:portee:designe] client_collectivite / RapportMaintenance : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit)
- [bloc:portee:designe] client_collectivite / DocumentEquipement : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit) [type=value_error, input_value={'app': {'nom': 'c2-clotu...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
