# Suivi des dossiers — ce que l'usine a compris

En bref : 1 rôle (Le responsable de la structure), 3 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le responsable de la structure (responsable de l'app)
- Voit tout, crée, modifie et supprime : Étapes de procédure (dans chaque Dossier)
- Voit tout, crée et modifie : Courriers types
- Dossiers : voit tout, en crée, les modifie, les fait passer de « demande de régularisation » à « enregistrement », les fait passer de « enregistrement » à « AR », les fait passer de « AR » à « échanges de mémoires », les fait passer de « échanges de mémoires » à « convocation audience »

## Les étapes

- Le dossier passe par : « demande de régularisation » → « enregistrement » → « AR » → « échanges de mémoires » → « convocation audience »
  - Le responsable de la structure fait passer de « demande de régularisation » à « enregistrement »
  - Le responsable de la structure fait passer de « enregistrement » à « AR »
  - Le responsable de la structure fait passer de « AR » à « échanges de mémoires »
  - Le responsable de la structure fait passer de « échanges de mémoires » à « convocation audience »

## Les informations de chaque fiche

- **Dossier** : Référence du dossier (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Nom du plaignant (texte court) · ☐ Objet de la plainte (texte long) · ☐ Date de réception de la plainte (date) · ☐ Date d'audience (date)
- **Étape de procédure** : Intitulé de l'étape (texte court) ◦ choisi par nous
  - relié à : dans chaque Dossier
  - proposé (à cocher) : ☐ Date de l'étape (date) · ☐ Date d'échéance (date) · ☐ Commentaire (texte long)
- **Courrier type** : Intitulé du courrier type (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Texte du modèle de courrier (texte long) · ☐ Destinataire type (texte court)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Dossier → « Référence du dossier » · Étape de procédure → « Intitulé de l'étape » · Courrier type → « Intitulé du courrier type »

## Pas encore dans notre stock (vos mots)

- Génération (édition) de courriers types à partir des dossiers — « édition de courrier ... éditer les courriers types »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Dossier:reference` = oui | <nouveau nom>  (Dossier → « Référence du dossier »)
- `nom:EtapeProcedure:intitule` = oui | <nouveau nom>  (Étape de procédure → « Intitulé de l'étape »)
- `nom:CourrierType:intitule` = oui | <nouveau nom>  (Courrier type → « Intitulé du courrier type »)
- `garder:Dossier:Nom du plaignant` = oui | non
- `garder:Dossier:Objet de la plainte` = oui | non
- `garder:Dossier:Date de réception de la plainte` = oui | non
- `garder:Dossier:Date d'audience` = oui | non
- `garder:EtapeProcedure:Date de l'étape` = oui | non
- `garder:EtapeProcedure:Date d'échéance` = oui | non
- `garder:EtapeProcedure:Commentaire` = oui | non
- `garder:CourrierType:Texte du modèle de courrier` = oui | non
- `garder:CourrierType:Destinataire type` = oui | non

### Pourquoi chaque droit

- responsable / EtapeProcedure : enfant de Dossier : même visibilité que le parent, géré par qui gère le parent — « La structure traite des dossiers (plaintes) » « suivant une procédure ( demande de régularisation, enregistrement, AR, échanges de mémoires, convocation audience »
- responsable / CourrierType : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « éditer les courriers types »
- responsable / Dossier : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre — « La structure traite des dossiers (plaintes) » « suivant une procédure ( demande de régularisation, enregistrement, AR, échanges de mémoires, convocation audience »
