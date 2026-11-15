# Gestion interventions — ce que l'usine a compris

En bref : 3 rôles (Le patron, La secrétaire, Le technicien), 9 sortes de fiches, 1 circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- relier chaque fiche opérateur à prestation, département : pas encore possible — lien retiré
- ⚠ Le technicien ne verra pas les départements qui le concernent (voir celles qui le désignent : pas encore possible)
- ⚠ Le technicien ne verra pas les interventions qui le concernent (voir celles qui le désignent : pas encore possible)

**Rien ne peut encore se construire sans en reparler ensemble.**

## Le visiteur (sans compte)
- Ne voit rien

## Le patron (responsable de l'app)
- Voit tout, crée, modifie et supprime : clients, sous-traitants, prestations, interventions, lignes de matériel/fourniture déposé (dans chaque intervention), lignes de sous-traitance (dans chaque intervention)
- Voit tout, modifie et supprime : départements, états d'intervention, fiches opérateur

## La secrétaire (invité par patron)
- Voit tout, crée, modifie et supprime : clients, sous-traitants, prestations, lignes de matériel/fourniture déposé (dans chaque intervention), lignes de sous-traitance (dans chaque intervention)
- Voit tout, modifie et supprime : départements, états d'intervention, fiches opérateur
- Interventions : voit tout, en crée, les modifie, les supprime, les fait passer de « en cours » à « effectuée » ou « annulée »

## Le technicien (invité par patron)
- Voit tout : prestations, états d'intervention
- Voit seulement les siennes : départements, interventions, lignes de matériel/fourniture déposé (dans chaque intervention), lignes de sous-traitance (dans chaque intervention)
- voit les clients affichés dans les interventions qu'il consulte (sans page à part)
- voit les sous-traitants affichés dans les lignes de sous-traitance qu'il consulte (sans page à part)
- a sa fiche opérateur, créée automatiquement

## Les étapes

- L'intervention commence « en cours » ; de « en cours », vers « effectuée » ou « annulée »
  - La secrétaire fait passer de « en cours » à « effectuée » ou « annulée »

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Adresse (texte long)
- **Sous-traitant** : Coordonnées (texte long)
  - proposé (à cocher) : ☐ Nom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Prestation** : Type/nature d’intervention (texte court) · Mots-clés (texte court)
  - proposé (à cocher) : ☐ Description (texte long)
- **Département** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Code département (texte court)
- **État d'intervention** : Libellé (choix parmi : en cours, effectuée, annulée) · Couleur (choix parmi : 🟠, 🟢, 🔴)
- **Fiche opérateur** : Nom (texte court) · Numéro de téléphone (téléphone)
  - relié à : prestation, département
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Email (e-mail)
- **Intervention** : Date (date) · Ville (texte court) · Montant des travaux (montant) · Montant de la facture (montant) · Pourcentage attribué au technicien (nombre)
  - relié à : client, fiche opérateur, prestation, département, état d'intervention
  - proposé (à cocher) : ☐ Adresse d’intervention (texte long) · ☐ Heure d’intervention (date et heure)
- **Ligne de matériel/fourniture déposé** : Matériel/fourniture déposé (texte court)
  - relié à : dans chaque intervention
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Montant (montant)
- **Ligne de sous-traitance** : Montant payé (montant)
  - relié à : dans chaque intervention, sous-traitant
  - proposé (à cocher) : ☐ Commentaire (texte long)

## Questions

- La secrétaire verra tous les clients, pas seulement ceux qui la concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les interventions qu'il voit; clôture : choisit les clients de ses interventions
- La secrétaire verra tous les sous-traitants, pas seulement ceux qui la concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les lignes de sous-traitance qu'il voit; clôture : choisit les sous-traitants de ses lignes de sous-traitance
- La secrétaire verra toutes les interventions, pas seulement celles qui la concernent — d'accord ? → **oui, nécessairement** : entité Intervention (registre) : l'initiateur (secretaire) doit être parmi ceux qui le tiennent
- Le technicien verra les clients (ex. nom, coordonnées) affichés dans les interventions qu'il traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les interventions qu'il voit
- Le technicien verra les sous-traitants (ex. nom, coordonnées) affichés dans les lignes de sous-traitance qu'il traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les lignes de sous-traitance qu'il voit
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : client → « Nom » · département → « Nom »
- « Seulement ceux qui le concernent » n'est pas encore possible : le technicien doit-il voir TOUS les départements ?
- « Seulement ceux qui le concernent » n'est pas encore possible : le technicien doit-il voir TOUS les interventions ?

## Pas encore dans notre stock (vos mots)

- Fonctionnement avec plusieurs connexions administrateur simultanées / exigence de performance — « capable de fonctionner correctement même avec plusieurs connexions administrateur simultanées »
- Affichage des interventions dans un calendrier — « générer une liste quotidienne des interventions sur le calendrier »
- Calcul de pourcentages et répartition du montant de facture — « Elle facilite le calcul des pourcentages, par exemple, en attribuant 20% du montant de la facture au technicien »
- Recherche multicritères par technicien, client, période, département, prestations ou mots-clés — « Les recherches peuvent être effectuées par technicien, client, période, département, prestations ou mots-clés de prestation »
- Envoi des interventions par SMS aux techniciens — « Les interventions sont envoyées directement par SMS sur le téléphone du technicien »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:secretaire:Client` = oui
- `registre_entier:secretaire:SousTraitant` = oui
- `registre_entier:secretaire:Intervention` = oui
- `vu_via:technicien:Client` = oui
- `vu_via:technicien:SousTraitant` = oui
- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:Departement:nom` = oui | <nouveau nom>  (département → « Nom »)
- `voir_tous:technicien:Departement` = oui | non
- `voir_tous:technicien:Intervention` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:SousTraitant:Nom` = oui | non
- `garder:SousTraitant:Téléphone` = oui | non
- `garder:SousTraitant:Email` = oui | non
- `garder:Prestation:Description` = oui | non
- `garder:Departement:Code département` = oui | non
- `garder:FicheOperateur:Prénom` = oui | non
- `garder:FicheOperateur:Email` = oui | non
- `garder:Intervention:Adresse d’intervention` = oui | non
- `garder:Intervention:Heure d’intervention` = oui | non
- `garder:LigneMaterielFourniture:Quantité` = oui | non
- `garder:LigneMaterielFourniture:Montant` = oui | non
- `garder:LigneSousTraitance:Commentaire` = oui | non

### Pourquoi chaque droit

- patron / Client : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « clients, types/nature d'interventions et techniciens » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- patron / SousTraitant : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « coordonnées et montants payés aux sous-traitants » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- patron / Prestation : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « prestations ou mots-clés de prestation » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- patron / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « liste quotidienne des interventions sur le calendrier » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- patron / LigneMaterielFourniture : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; enfant de intervention : même visibilité que le parent, géré par qui gère le parent — « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « liste quotidienne des interventions sur le calendrier »
- patron / LigneSousTraitance : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; enfant de intervention : même visibilité que le parent, géré par qui gère le parent — « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « liste quotidienne des interventions sur le calendrier »
- patron / Departement : préréglage catalogue : visible de tous les connectés ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « département » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- patron / EtatIntervention : préréglage catalogue : visible de tous les connectés ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « en cours (🟠), effectuée (🟢), annulée (🔴) » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- patron / FicheOperateur : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; clôture : voit ce qu'il modifie — « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- secretaire / Client : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « clients, types/nature d'interventions et techniciens » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- secretaire / SousTraitant : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « coordonnées et montants payés aux sous-traitants » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- secretaire / Prestation : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « prestations ou mots-clés de prestation » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- secretaire / LigneMaterielFourniture : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; enfant de intervention : même visibilité que le parent, géré par qui gère le parent — « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « liste quotidienne des interventions sur le calendrier » « Chaque intervention est associée à un état coloré : en cours (🟠), effectuée (🟢), annulée (🔴) »
- secretaire / LigneSousTraitance : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; enfant de intervention : même visibilité que le parent, géré par qui gère le parent — « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « liste quotidienne des interventions sur le calendrier » « Chaque intervention est associée à un état coloré : en cours (🟠), effectuée (🟢), annulée (🔴) »
- secretaire / Departement : préréglage catalogue : visible de tous les connectés ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « département » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- secretaire / EtatIntervention : préréglage catalogue : visible de tous les connectés ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « en cours (🟠), effectuée (🟢), annulée (🔴) » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- secretaire / FicheOperateur : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; clôture : voit ce qu'il modifie — « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- secretaire / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » — « liste quotidienne des interventions sur le calendrier » « Chaque intervention est associée à un état coloré : en cours (🟠), effectuée (🟢), annulée (🔴) » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron » « Seuls les administrateurs peuvent modifier ou supprimer des données via une interface unique, accessible au secrétariat et au patron »
- technicien / Prestation : préréglage catalogue : visible de tous les connectés ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « prestations ou mots-clés de prestation » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- technicien / EtatIntervention : préréglage catalogue : visible de tous les connectés ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » — « en cours (🟠), effectuée (🟢), annulée (🔴) » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- technicien / Departement : préréglage catalogue : visible de tous les connectés ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « leurs secteurs d'activités et d'interventions par département » — « département » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données » « leurs secteurs d'activités et d'interventions par département »
- technicien / Intervention : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Les interventions sont envoyées directement par SMS sur le téléphone du technicien » — « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Les interventions sont envoyées directement par SMS sur le téléphone du technicien »
- technicien / LigneMaterielFourniture : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; enfant de intervention : même visibilité que le parent — « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Les interventions sont envoyées directement par SMS sur le téléphone du technicien »
- technicien / LigneSousTraitance : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; enfant de intervention : même visibilité que le parent — « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Les interventions sont envoyées directement par SMS sur le téléphone du technicien »
- technicien / Client : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; clôture : affiché dans les interventions qu'il voit — « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- technicien / SousTraitant : exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; clôture : affiché dans les lignes de sous-traitance qu'il voit — « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données »
- technicien / FicheOperateur : préréglage profil : sa propre fiche, créée automatiquement ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Seuls les administrateurs peuvent modifier ou supprimer des données » ; exception : « Les techniciens ont leur propre interface unique, avec leurs informations personnelles (fiche opérateur, nom, numéro de téléphone) » — « fiche opérateur, nom, numéro de téléphone » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Seuls les administrateurs peuvent modifier ou supprimer des données » « Les techniciens ont leur propre interface unique, avec leurs informations personnelles (fiche opérateur, nom, numéro de téléphone) »

### Refus — blocs : lien:profil, portee:designe

- [bloc:lien:profil] FicheOperateur : un profil qui désigne une autre fiche (Prestation, Departement) arrive en N1.3 (bloc « lien depuis un profil » pas encore construit)
- [bloc:portee:designe] technicien / Departement : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit)
- [bloc:portee:designe] technicien / Intervention : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit) [type=value_error, input_value={'app': {'nom': 'c2-depan...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error

Variante NON proposée : elle donnerait des droits que le brief refuse —
- technicien / Departement : voir (own → all)
