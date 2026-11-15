# Gestion des interventions — ce que l'usine a compris

En bref : 3 rôles (Le patron, La secrétaire, Le technicien), 5 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le patron (responsable de l'app)
- Voit tout, modifie et supprime : Techniciens
- Voit tout, crée, modifie et supprime : Clients, Types d'intervention, Sous-traitants, Interventions

## La secrétaire (invité par patron)
- Voit tout, modifie et supprime : Techniciens
- Voit tout, crée, modifie et supprime : Clients, Types d'intervention, Sous-traitants
- Interventions : voit tout, en crée, les modifie, les supprime, les fait passer de « en cours » à « effectuée » ou « annulée »

## Le technicien (invité par patron)
- Voit tout : Types d'intervention
- a son Technicien, créé automatiquement

## Les étapes

- L'intervention commence « en cours » ; de « en cours », vers « effectuée » ou « annulée »
  - La secrétaire fait passer de « en cours » à « effectuée » ou « annulée »

## Les informations de chaque fiche

- **Technicien** : Nom (texte court) · Numéro de téléphone (téléphone) · Secteurs d'activités (texte court) · Départements d'intervention (texte court)
  - proposé (à cocher) : ☐ Fiche opérateur (contenu à préciser) (texte long) · ☐ Prénom (texte court) · ☐ Pourcentage habituel sur facture (nombre)
- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Adresse (texte long) · ☐ Ville (texte court) · ☐ Email (e-mail)
- **Type d'intervention** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long) · ☐ Tarif de base (montant)
- **Sous-traitant** : Nom (texte court) ◦ choisi par nous · Coordonnées (texte long)
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Spécialité (texte court)
- **Intervention** : Date de l'intervention (date) · Département (texte court) · Montant des travaux (montant) · Matériels/fournitures déposés (texte long, facultatif) · Montant de la facture (montant, facultatif) · Pourcentage attribué au technicien (nombre) · Montant payé au sous-traitant (montant, facultatif)
  - relié à : Client, Type d'intervention, Technicien, Sous-traitant
  - proposé (à cocher) : ☐ Heure de l'intervention (date et heure) · ☐ Adresse / ville de l'intervention (texte court) · ☐ Description de la prestation (texte long) · ☐ Montant des matériels/fournitures (montant) · ☐ Part du technicien (montant)

## Questions

- La secrétaire verra tous les Clients, pas seulement ceux qui la concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Interventions qu'il voit; clôture : choisit les Clients de ses Interventions
- La secrétaire verra tous les Sous-traitants, pas seulement ceux qui la concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Interventions qu'il voit; clôture : choisit les Sous-traitants de ses Interventions
- La secrétaire verra toutes les Interventions, pas seulement celles qui la concernent — d'accord ? → **oui, nécessairement** : entité Intervention (registre) : l'initiateur (secretaire) doit être parmi ceux qui le tiennent
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Client → « Nom » · Type d'intervention → « Intitulé » · Sous-traitant → « Nom »

## Pas encore dans notre stock (vos mots)

- Vue calendrier avec une liste quotidienne des interventions — « générer une liste quotidienne des interventions sur le calendrier »
- Calcul de pourcentages sur le montant facturé (par exemple 20 % pour le technicien) — « facilite le calcul des pourcentages, par exemple, en attribuant 20% du montant de la facture au technicien »
- Recherche multicritère (technicien, client, période, département, prestations, mots-clés) — « Les recherches peuvent être effectuées par technicien, client, période, département, prestations ou mots-clés de prestation »
- Envoi des interventions par SMS au technicien — « Les interventions sont envoyées directement par SMS sur le téléphone du technicien »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:secretaire:Client` = oui
- `registre_entier:secretaire:SousTraitant` = oui
- `registre_entier:secretaire:Intervention` = oui
- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `nom:TypeIntervention:intitule` = oui | <nouveau nom>  (Type d'intervention → « Intitulé »)
- `nom:SousTraitant:nom` = oui | <nouveau nom>  (Sous-traitant → « Nom »)
- `garder:Technicien:Fiche opérateur (contenu à préciser)` = oui | non
- `garder:Technicien:Prénom` = oui | non
- `garder:Technicien:Pourcentage habituel sur facture` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Client:Ville` = oui | non
- `garder:Client:Email` = oui | non
- `garder:TypeIntervention:Description` = oui | non
- `garder:TypeIntervention:Tarif de base` = oui | non
- `garder:SousTraitant:Téléphone` = oui | non
- `garder:SousTraitant:Email` = oui | non
- `garder:SousTraitant:Spécialité` = oui | non
- `garder:Intervention:Heure de l'intervention` = oui | non
- `garder:Intervention:Adresse / ville de l'intervention` = oui | non
- `garder:Intervention:Description de la prestation` = oui | non
- `garder:Intervention:Montant des matériels/fournitures` = oui | non
- `garder:Intervention:Part du technicien` = oui | non

### Pourquoi chaque droit

- patron / Technicien : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; clôture : voit ce qu'il modifie — « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- patron / Client : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « mettant en relation clients, types/nature d'interventions et techniciens » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- patron / TypeIntervention : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « prestations ou mots-clés de prestation » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- patron / SousTraitant : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « les coordonnées et montants payés aux sous-traitants » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- patron / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « une liste quotidienne des interventions sur le calendrier, triée par date, client et technicien, avec le montant des travaux » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- secretaire / Technicien : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; clôture : voit ce qu'il modifie — « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- secretaire / Client : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « mettant en relation clients, types/nature d'interventions et techniciens » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- secretaire / TypeIntervention : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « prestations ou mots-clés de prestation » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- secretaire / SousTraitant : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « les coordonnées et montants payés aux sous-traitants » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- secretaire / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « une liste quotidienne des interventions sur le calendrier, triée par date, client et technicien, avec le montant des travaux » « Chaque intervention est associée à un état coloré : en cours (🟠), effectuée (🟢), annulée (🔴) » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- technicien / TypeIntervention : préréglage catalogue : visible de tous les connectés ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « prestations ou mots-clés de prestation » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- technicien / Technicien : préréglage profil : sa propre fiche, créée automatiquement ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Les techniciens ont leur propre interface unique, avec leurs informations personnelles » — « Les techniciens ont leur propre interface unique, avec leurs informations personnelles (fiche opérateur, nom, numéro de téléphone) » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Les techniciens ont leur propre interface unique, avec leurs informations personnelles »
