# Suivi des livraisons — ce que l'usine a compris

En bref : 2 rôles (Le responsable, Le chauffeur), 6 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le responsable (responsable de l'app)
- Voit tout : Chauffeurs, Véhicules
- Voit tout, crée et modifie : Entreprises clientes, Sous-traitants, Livraisons
- Voit tout, crée, modifie et supprime : Documents de livraison (dans chaque Livraison)

## Le chauffeur (invité par responsable)
- Voit seulement les siennes, crée et modifie : Véhicules
- Voit tout : Entreprises clientes
- Voit tout, crée, modifie et supprime : Documents de livraison (dans chaque Livraison)
- a son Chauffeur, créé automatiquement, qu'il peut modifier
- Livraisons : voit tout, en crée, les modifie, les fait passer de « demandée » à « confirmée »

## Les étapes

- La livraison passe par : « demandée » → « confirmée »
  - Le chauffeur fait passer de « demandée » à « confirmée »

## Les informations de chaque fiche

- **Chauffeur** : Nom (texte court) ◦ choisi par nous · Disponibilités (texte long)
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone)
- **Véhicule** : Immatriculation (texte court) ◦ choisi par nous · Capacité (nombre)
  - proposé (à cocher) : ☐ Type de véhicule (texte court) · ☐ Unité de capacité (kg, m³, palettes) (texte court)
- **Entreprise cliente** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Adresse (texte long) · ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Sous-traitant** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Livraison** : Trajet (texte court) · Horaire (date et heure) · Marchandises dangereuses (oui / non)
  - relié à : Entreprise cliente, Chauffeur, Véhicule
  - proposé (à cocher) : ☐ Adresse d'enlèvement (texte long) · ☐ Adresse de livraison (texte long) · ☐ Description de la marchandise (texte long) · ☐ Poids ou volume de la marchandise (nombre) · ☐ Date de livraison effective (date et heure)
- **Document de livraison** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque Livraison
  - proposé (à cocher) : ☐ Fichier ou lien du document (lien web) · ☐ Document vérifié (oui / non) · ☐ Date de validité (date)

## Questions

- Le chauffeur verra toutes les Entreprises clientes, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Livraisons qu'il voit; clôture : choisit les Entreprises clientes de ses Livraisons
- Le chauffeur verra toutes les Livraisons, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : voit ce qu'il modifie
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Chauffeur → « Nom » · Véhicule → « Immatriculation » · Entreprise cliente → « Nom » · Sous-traitant → « Nom » · Document de livraison → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Application mobile pour les chauffeurs — « Création d'application mobile pour transporteur ... le développement d'une application mobile qui centraliserait les informations de livraison »
- Diffusion directe et en temps réel des informations et des statuts de livraison aux chauffeurs — « les diffuserait directement aux chauffeurs, permettant ainsi une mise à jour en temps réel des statuts de livraison »
- Choix des trajets et des horaires par les chauffeurs selon leurs disponibilités et la capacité de leurs véhicules (planning des missions) — « choisir leurs trajets et horaires en fonction de leurs disponibilités et de la capacité de leurs véhicules »
- Notifications automatiques envoyées lorsqu'une entreprise a une demande de transport — « des notifications automatiques qui se déclencherais lorsqu'une entreprise aura une demande de transport à faire »
- Suivi en temps réel des livraisons (localisation, avancement) — « un suivi en temps réel des livraisons »
- Vérification systématique et automatique des documents obligatoires, notamment pour les marchandises dangereuses — « vérifierait systématiquement les documents nécessaires, notamment pour les marchandises dangereuses »
- Gestion des documents de transport rattachés aux livraisons (pièces justificatives) — « les documents nécessaires, notamment pour les marchandises dangereuses »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:chauffeur:EntrepriseCliente` = oui
- `registre_entier:chauffeur:Livraison` = oui
- `nom:Chauffeur:nom` = oui | <nouveau nom>  (Chauffeur → « Nom »)
- `nom:Vehicule:immatriculation` = oui | <nouveau nom>  (Véhicule → « Immatriculation »)
- `nom:EntrepriseCliente:nom` = oui | <nouveau nom>  (Entreprise cliente → « Nom »)
- `nom:SousTraitant:nom` = oui | <nouveau nom>  (Sous-traitant → « Nom »)
- `nom:DocumentLivraison:intitule` = oui | <nouveau nom>  (Document de livraison → « Intitulé »)
- `garder:Chauffeur:Prénom` = oui | non
- `garder:Chauffeur:Téléphone` = oui | non
- `garder:Vehicule:Type de véhicule` = oui | non
- `garder:Vehicule:Unité de capacité (kg, m³, palettes)` = oui | non
- `garder:EntrepriseCliente:Adresse` = oui | non
- `garder:EntrepriseCliente:Téléphone` = oui | non
- `garder:EntrepriseCliente:Email` = oui | non
- `garder:SousTraitant:Téléphone` = oui | non
- `garder:SousTraitant:Email` = oui | non
- `garder:Livraison:Adresse d'enlèvement` = oui | non
- `garder:Livraison:Adresse de livraison` = oui | non
- `garder:Livraison:Description de la marchandise` = oui | non
- `garder:Livraison:Poids ou volume de la marchandise` = oui | non
- `garder:Livraison:Date de livraison effective` = oui | non
- `garder:DocumentLivraison:Fichier ou lien du document` = oui | non
- `garder:DocumentLivraison:Document vérifié` = oui | non
- `garder:DocumentLivraison:Date de validité` = oui | non

### Pourquoi chaque droit

- responsable / Chauffeur : clôture : affiché dans les Livraisons qu'il voit ; clôture : choisit les Chauffeurs de ses Livraisons — « centraliserait les informations de livraison et les diffuserait directement aux chauffeurs »
- responsable / Vehicule : clôture : affiché dans les Livraisons qu'il voit ; clôture : choisit les Véhicules de ses Livraisons — « centraliserait les informations de livraison et les diffuserait directement aux chauffeurs »
- responsable / EntrepriseCliente : tient le registre (supprimer : seulement si le brief le dit) — « lorsqu'une entreprise aura une demande de transport à faire »
- responsable / SousTraitant : tient le registre (supprimer : seulement si le brief le dit) — « la difficulté à coordonner nos sous-traitants »
- responsable / Livraison : tient le registre (supprimer : seulement si le brief le dit) — « centraliserait les informations de livraison et les diffuserait directement aux chauffeurs »
- responsable / DocumentLivraison : enfant de Livraison : même visibilité que le parent, géré par qui gère le parent — « centraliserait les informations de livraison et les diffuserait directement aux chauffeurs »
- chauffeur / Vehicule : préréglage collection : le propriétaire crée et modifie les siens — « la capacité de leurs véhicules »
- chauffeur / EntrepriseCliente : clôture : affiché dans les Livraisons qu'il voit ; clôture : choisit les Entreprises clientes de ses Livraisons — « centraliserait les informations de livraison et les diffuserait directement aux chauffeurs »
- chauffeur / DocumentLivraison : enfant de Livraison : même visibilité que le parent, géré par qui gère le parent — « centraliserait les informations de livraison et les diffuserait directement aux chauffeurs » « lorsqu'une entreprise aura une demande de transport à faire » « offrirait également aux chauffeurs la possibilité de choisir leurs trajets et horaires »
- chauffeur / Chauffeur : préréglage profil : sa propre fiche, créée automatiquement — « aux chauffeurs la possibilité de choisir leurs trajets et horaires en fonction de leurs disponibilités »
- chauffeur / Livraison : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « centraliserait les informations de livraison et les diffuserait directement aux chauffeurs » ; exception : « offrirait également aux chauffeurs la possibilité de choisir leurs trajets et horaires » — « centraliserait les informations de livraison et les diffuserait directement aux chauffeurs » « lorsqu'une entreprise aura une demande de transport à faire » « centraliserait les informations de livraison et les diffuserait directement aux chauffeurs » « offrirait également aux chauffeurs la possibilité de choisir leurs trajets et horaires »
