# Suivi des dossiers — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, Le client), aucun sorte de fiches, aucun circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- ⚠ Le client ne verra pas les Documents qui le concernent (voir celles qui le désignent : pas encore possible)
- les dossiers que l'administrateur saisit pour le client : pas encore possible — retirées

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Ne voit rien

## Le client (invité par administrateur)
- Ne voit rien

## Les informations de chaque fiche


## Questions

- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Génération automatique de documents (contrats, lettres, factures) — « génération automatique de documents (contrats, lettres, »
- Gestion documentaire : ajout et visualisation de documents (pièces jointes), côté administration et côté client — « gestion documentaire (ajout, visualisation »
- Notifications liées aux documents, côté administration et côté client — « visualisation, notifications) »
- Prestations d'accompagnement : mise en place, formation et documentation utilisateur — « Mise en place, formation et documentation utilisateur. »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `accepter_proposition` = oui | non

### Pourquoi chaque droit


### Refus — blocs : lien:pour-autrui, portee:designe

- [bloc:lien:pour-autrui] Dossier : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x)
- [bloc:portee:designe] client / Document : « les siennes » sur des fiches qu'il ne possède pas (sans propriétaire) — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit) [type=value_error, input_value={'app': {'nom': 'c2-suivi...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
