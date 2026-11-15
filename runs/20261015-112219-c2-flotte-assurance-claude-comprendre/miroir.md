# Gestion de flotte — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, Le souscripteur), 2 sortes de fiches, aucun circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- ⚠ Le souscripteur ne verra pas les véhicules qui le concernent (voir celles qui le désignent : pas encore possible)
- L'administrateur crée le compte des souscripteurs : pas encore possible (les invitations arrivent avec la connexion)
- les contrats que l'administrateur saisit pour le souscripteur : pas encore possible — retirées

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, modifie et supprime : souscripteurs
- a son administrateur, créé automatiquement, qu'il peut modifier

## Le souscripteur (invité par administrateur)
- a son souscripteur, créé automatiquement, qu'il peut modifier

## Les informations de chaque fiche

- **Administrateur** : Identifiant (texte court) · Mot de passe (texte court) · Adresse email (e-mail)
  - proposé (à cocher) : ☐ Nom (texte court)
- **Souscripteur** : Raison sociale (texte court) · Identifiant (texte court) · Mot de passe (texte court) · Adresse (texte court) · Code postal (texte court) · Ville (texte court) · Email (e-mail)
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email de l'agence (e-mail)

## Questions

- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Génération en PDF d'une carte verte à imprimer, avec un contenu imposé (modèle dans un PDF joint) — « permettre d’imprimer une carte verte (vie génération pdf)... La carte verte doit contenir les infos suivantes (voir PDF joint) »
- Envoi automatique d'un e-mail à l'agence et au client à chaque action (sauf l'impression de la carte verte) — « Lors de chaque action (sauf impression carte verte), un mail doit être envoyé à l’agence et au client. »
- Import d'un fichier Excel par l'administrateur pour alimenter la flotte — « Avec possibilité d’import fichier excel pour alimenter la flotte »
- Export du parc de véhicules vers Excel — « possibilité export parc sur excel »
- Filtre d'affichage des véhicules selon qu'ils sont sortis ou non — « possibilité de filtrer l’affichage des véhicules si sortis ou non »
- Contrainte technique : application en PHP/MySQL installable sur un hébergement mutualisé OVH — « Interface php/mysql pouvant être installé sur hébergement mutualisé OVH. »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `accepter_proposition` = oui | non
- `garder:Administrateur:Nom` = oui | non
- `garder:Souscripteur:Téléphone` = oui | non
- `garder:Souscripteur:Email de l'agence` = oui | non

### Pourquoi chaque droit

- administrateur / Souscripteur : exception : « Création / modification / suppression : de souscripteur et de flotte » ; exception : « Création / modification / suppression : de souscripteur et de flotte » ; clôture : voit ce qu'il modifie — « Création / modification / suppression : de souscripteur et de flotte » « Création / modification / suppression : de souscripteur et de flotte »
- administrateur / Administrateur : préréglage profil : sa propre fiche, créée automatiquement — « Identifiant et mot de passe »
- souscripteur / Souscripteur : préréglage profil : sa propre fiche, créée automatiquement — « Création / modification / suppression : de souscripteur et de flotte »

### Refus — blocs : acteur:invitation, lien:pour-autrui, portee:designe

- [bloc:lien:pour-autrui] Contrat : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x)
- [bloc:acteur:invitation] administrateur / Souscripteur : créer le compte d'une autre personne, c'est l'inviter — arrive avec la connexion et l'équipe (N1.5)
- [bloc:portee:designe] souscripteur / Vehicule : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit) [type=value_error, input_value={'app': {'nom': 'c2-flott...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
