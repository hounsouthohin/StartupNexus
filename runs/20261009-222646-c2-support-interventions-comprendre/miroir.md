# Gestion interventions — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, L'agent), 5 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout : clients
- Voit tout, crée et modifie : entrées de knowledge base
- a son compte administrateur, créé automatiquement, qu'il peut modifier
- Interventions : voit tout, en crée, les modifie, les supprime quand elles sont « traité », les fait passer de « traité » à « commenté » ou « mis dans une knowledge base » ou « supprimé »

## L'agent (invité par administrateur)
- Voit tout, crée et modifie : clients
- Voit tout : entrées de knowledge base
- a son compte agent, créé automatiquement, qu'il peut modifier
- Interventions : voit tout, en crée, les modifie, les fait passer de « enregistré » à « envoyé », les fait passer de « envoyé » à « traité »

## Les étapes

- L'intervention commence « enregistré » ; de « enregistré », vers « envoyé » ; de « envoyé », vers « traité » ; de « traité », vers « supprimé » ou « commenté » ou « mis dans une knowledge base »
  - L'administrateur fait passer de « traité » à « commenté » ou « mis dans une knowledge base » ou « supprimé »
  - L'agent fait passer de « enregistré » à « envoyé »
  - L'agent fait passer de « envoyé » à « traité »

## Les informations de chaque fiche

- **Compte agent** : Permissions (texte court)
  - proposé (à cocher) : ☐ Identifiant de connexion (texte court) · ☐ Email (e-mail)
- **Compte administrateur** : Permissions (texte court)
  - proposé (à cocher) : ☐ Identifiant de connexion (texte court) · ☐ Email (e-mail)
- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Intervention** : Description du problème (texte long) · Date (date) · Commentaire (texte long, facultatif)
  - relié à : client
  - proposé (à cocher) : ☐ Priorité (texte court) · ☐ Catégorie de problème (texte court)
- **Entrée de knowledge base** : Titre (texte court) ◦ choisi par nous
  - relié à : intervention
  - proposé (à cocher) : ☐ Résumé (texte long) · ☐ Mots-clés (texte court)

## Questions

- L'agent verra tous les clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Client (registre) : il faut au moins un acteur qui le tient (« manager »)
- L'agent verra toutes les interventions, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : entité Intervention (registre) : l'initiateur (agent) doit être parmi ceux qui le tiennent
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : client → « Nom » · entrée de knowledge base → « Titre »

## Pas encore dans notre stock (vos mots)

- Sécurisation SSL de l'authentification — « interface d'authentification entièrement sécurisé en SSL »
- Recherche de formulaires — « gestion complète des formulaire (recherche,modifcation,ajout supprission...) »
- Classement des interventions par date — « toutes les interventions sont classés par date »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:agent:Client` = oui
- `registre_entier:agent:Intervention` = oui
- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:EntreeKnowledgeBase:titre` = oui | <nouveau nom>  (entrée de knowledge base → « Titre »)
- `garder:CompteAgent:Identifiant de connexion` = oui | non
- `garder:CompteAgent:Email` = oui | non
- `garder:CompteAdministrateur:Identifiant de connexion` = oui | non
- `garder:CompteAdministrateur:Email` = oui | non
- `garder:Client:Prénom` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Intervention:Priorité` = oui | non
- `garder:Intervention:Catégorie de problème` = oui | non
- `garder:EntreeKnowledgeBase:Résumé` = oui | non
- `garder:EntreeKnowledgeBase:Mots-clés` = oui | non

### Pourquoi chaque droit

- administrateur / Client : responsable de l'app : voit les registres de l'équipe (lecture) — « description du problème d'un client »
- administrateur / EntreeKnowledgeBase : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « mettre dans une knowledge base pour se servir comme référence en cas de problème similaire »
- administrateur / CompteAdministrateur : préréglage profil : sa propre fiche, créée automatiquement — « on peut s'enregister et cérer des comptes utilisatuers avec des permissions différentes »
- administrateur / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; fait l'étape depuis « traite » ; exception : « l'administrateur possède le choix soit de la supprimier,commenté ou mettre dans une knowledge base » ; exception : « l'administrateur possède le choix soit de la supprimier,commenté ou mettre dans une knowledge base » ; exception : « l'administrateur possède le choix soit de la supprimier,commenté ou mettre dans une knowledge base » — « un agent peut alors remplir un formulaire contenant une description du problème d'un client ,ce  formulaire peut ensuite être enregistré dans la base » « dès que l'agent a traité une intervention celle ci est marqué comme traité et l'administrateur possède le choix soit de la supprimier,commenté ou mettre dans une knowledge base » « l'administrateur possède le choix soit de la supprimier,commenté ou mettre dans une knowledge base » « l'administrateur possède le choix soit de la supprimier,commenté ou mettre dans une knowledge base » « l'administrateur possède le choix soit de la supprimier,commenté ou mettre dans une knowledge base »
- agent / Client : tient le registre (supprimer : seulement si le brief le dit) — « description du problème d'un client »
- agent / EntreeKnowledgeBase : préréglage catalogue : visible de tous les connectés — « mettre dans une knowledge base pour se servir comme référence en cas de problème similaire »
- agent / CompteAgent : préréglage profil : sa propre fiche, créée automatiquement — « on peut s'enregister et cérer des comptes utilisatuers avec des permissions différentes »
- agent / Intervention : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « un agent peut alors remplir un formulaire contenant une description du problème d'un client » ; exception : « l'agent a traité une intervention celle ci est marqué comme traité » — « un agent peut alors remplir un formulaire contenant une description du problème d'un client ,ce  formulaire peut ensuite être enregistré dans la base » « dès que l'agent a traité une intervention celle ci est marqué comme traité et l'administrateur possède le choix soit de la supprimier,commenté ou mettre dans une knowledge base » « un agent peut alors remplir un formulaire contenant une description du problème d'un client » « l'agent a traité une intervention celle ci est marqué comme traité »
