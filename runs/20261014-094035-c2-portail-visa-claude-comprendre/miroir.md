# Suivi des visas — ce que l'usine a compris

En bref : 2 rôles (Le responsable, Le client), 1 sorte de fiches, aucun circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- les dossiers que le responsable saisit pour le client : pas encore possible — retirées

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## Le responsable (responsable de l'app)
- Ne voit rien

## Le client (s'inscrit lui-même)
- a son Client, créé automatiquement, qu'il peut modifier

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous · Email (e-mail)
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Nationalité (texte court)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Client → « Nom »
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Relier la base Airtable existante (Clients, Dossiers) a Softr — « Relier Airtable (base de données) à Softr »
- Livrer l'application dans l'outil no-code Softr impose par le client — « Application Softr fonctionnelle et sécurisée »
- Page tableau de bord pour le client — « Tableau de bord client »
- Documents du dossier televerses par le client — « documents ... Téléversement des documents par le client »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `accepter_proposition` = oui | non
- `garder:Client:Prénom` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Nationalité` = oui | non

### Pourquoi chaque droit

- client / Client : préréglage profil : sa propre fiche, créée automatiquement — « se connecter avec email + mot de passe »

### Refus — blocs : lien:pour-autrui

- [bloc:lien:pour-autrui] Dossier : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x) [type=value_error, input_value={'app': {'nom': 'c2-porta...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
