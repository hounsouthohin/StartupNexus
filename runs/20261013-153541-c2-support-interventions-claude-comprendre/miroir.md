# Gestion des interventions — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, L'agent), 4 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : Clients, Articles de la base de connaissances
- Interventions : voit tout, en crée, les modifie, les supprime quand elles sont « traitée »

## L'agent (invité par administrateur)
- Voit tout, crée et modifie : Clients
- Voit tout : Articles de la base de connaissances
- a son Agent, créé automatiquement, qu'il peut modifier
- Interventions : voit tout, en crée, les modifie, les fait passer de « enregistrée » à « envoyée au centre de traitement », les fait passer de « envoyée au centre de traitement » à « traitée »

## Les étapes

- L'intervention passe par : « enregistrée » → « envoyée au centre de traitement » → « traitée »
  - L'agent fait passer de « enregistrée » à « envoyée au centre de traitement »
  - L'agent fait passer de « envoyée au centre de traitement » à « traitée »

## Les informations de chaque fiche

- **Agent** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Service ou équipe (texte court)
- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long) · ☐ Numéro de contrat ou d'abonné (texte court)
- **Intervention** : Description du problème (texte long) · Commentaire de l'administrateur (texte long, facultatif)
  - relié à : Client
  - proposé (à cocher) : ☐ Date de l'intervention (date) · ☐ Priorité (choix) · ☐ Catégorie du problème (texte court) · ☐ Solution apportée (texte long)
- **Article de la base de connaissances** : Titre (texte court) ◦ choisi par nous
  - relié à : Intervention
  - proposé (à cocher) : ☐ Solution de référence (texte long) · ☐ Mots-clés (texte court)

## Questions

- L'agent verra tous les Clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Interventions qu'il voit; clôture : choisit les Clients de ses Interventions
- L'agent verra toutes les Interventions, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : entité Intervention (registre) : l'initiateur (agent) doit être parmi ceux qui le tiennent
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Agent → « Nom » · Client → « Nom » · Article de la base de connaissances → « Titre »

## Pas encore dans notre stock (vos mots)

- Recherche dans les formulaires d'intervention — « gestion complète des formulaire (recherche »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:agent:Client` = oui
- `registre_entier:agent:Intervention` = oui
- `nom:Agent:nom` = oui | <nouveau nom>  (Agent → « Nom »)
- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `nom:ArticleConnaissance:titre` = oui | <nouveau nom>  (Article de la base de connaissances → « Titre »)
- `garder:Agent:Prénom` = oui | non
- `garder:Agent:Téléphone` = oui | non
- `garder:Agent:Service ou équipe` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Client:Numéro de contrat ou d'abonné` = oui | non
- `garder:Intervention:Date de l'intervention` = oui | non
- `garder:Intervention:Priorité` = oui | non
- `garder:Intervention:Catégorie du problème` = oui | non
- `garder:Intervention:Solution apportée` = oui | non
- `garder:ArticleConnaissance:Solution de référence` = oui | non
- `garder:ArticleConnaissance:Mots-clés` = oui | non

### Pourquoi chaque droit

- administrateur / Client : tient le registre (supprimer : seulement si le brief le dit) — « une description du problème d'un client »
- administrateur / ArticleConnaissance : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) ; exception : « l'administrateur possède le choix soit de la supprimier,commenté ou mettre dans une knowledge base » — « mettre dans une knowledge base pour se servir comme référence en cas de problème similaire » « l'administrateur possède le choix soit de la supprimier,commenté ou mettre dans une knowledge base »
- administrateur / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; exception : « celle ci est marqué comme traité et l'administrateur possède le choix soit de la supprimier » — « un agent peut alors remplir un formulaire contenant une description du problème d'un client » « celle ci est marqué comme traité et l'administrateur possède le choix soit de la supprimier »
- agent / Client : tient le registre (supprimer : seulement si le brief le dit) — « une description du problème d'un client »
- agent / ArticleConnaissance : préréglage catalogue : visible de tous les connectés — « mettre dans une knowledge base pour se servir comme référence en cas de problème similaire »
- agent / Agent : préréglage profil : sa propre fiche, créée automatiquement — « une fois enregistré dans la base de donnée un agent »
- agent / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « un agent peut alors remplir un formulaire contenant une description du problème d'un client » ; exception : « dès que l'agent a traité une intervention celle ci est marqué comme traité » — « un agent peut alors remplir un formulaire contenant une description du problème d'un client » « formulaire peut ensuite être enregistré dans la base,envoyé au centre de traitement pour y être traité » « un agent peut alors remplir un formulaire contenant une description du problème d'un client » « dès que l'agent a traité une intervention celle ci est marqué comme traité »
