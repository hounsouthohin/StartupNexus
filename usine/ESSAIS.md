# Essayer une app de l'usine, à la main

Tu joues le client et ses utilisateurs. Tes retours sont la **boussole de valeur** : les juges de l'usine
disent si l'app respecte ce qu'elle a compris, toi tu dis si elle **sert**.

## 1. Lancer l'app

1. Docker Desktop doit tourner (c'est lui qui porte la base de données).
2. Dans un terminal, à la racine du projet :

   ```
   python -m usine demarrer runs/<dossier-de-l-app> --depart
   ```

   puis ouvrir **http://localhost:3300**. `Ctrl+C` arrête l'app.
   - `--depart` remet les données de départ (tout ce que tu as saisi est effacé) : à mettre pour repartir de zéro.
   - Une app à la fois sur le port 3300 (sinon `--port 3301`).
3. La liste des apps à essayer, avec leur commande, est dans `runs/<…-repetition-reelle>/a-tester.md`.

## 2. Lire avant d'essayer (5 min)

- `brief.txt` : ce que le client a écrit, mot pour mot.
- `miroir.md` : ce que l'usine a compris (qui fait quoi), les informations retenues, les questions
  qu'elle poserait au client, et ce qui n'est **pas encore dans notre stock**.

Les deux sont dans le dossier `runs/<…-comprendre>/` indiqué dans `a-tester.md`.

## 3. Se connecter

La connexion est **simulée** (pas de mot de passe, la vraie arrive en N1.5) : sur la page d'accueil,
choisis un rôle et **personne 1** ou **personne 2**. L'en-tête affiche qui tu es. « visiteur » = non connecté.

## 4. Quoi essayer (30 à 45 min par app)

1. **Chaque rôle, à tour de rôle** : le menu montre-t-il ce que ce rôle doit voir d'après le brief ?
2. **Le travail réel** : crée les fiches dans l'ordre naturel (un client, puis son dossier…), remplis les
   formulaires, fais avancer les étapes (boutons « Valider », « Refuser »…).
3. **La séparation** : la personne 1 crée des fiches ; connecte-toi en personne 2 du même rôle — les voit-elle ?
   Le devrait-elle ?
4. **Modifier, supprimer** : permis quand il le faut, refusé sinon ? Le message est-il clair ?
5. **Tricher** : essaie ce qu'un rôle ne devrait pas pouvoir faire.
6. **Les mots** : noms des fiches, des champs, des boutons — un vrai utilisateur les comprendrait-il ?
7. **Demain matin** : que manque-t-il pour que ce client utilise vraiment l'app ?

## 5. Déjà connu (inutile de le signaler — mais dis-le si ça empêche de s'en servir)

- La connexion simulée.
- Ce que le miroir range dans « Pas encore dans notre stock » : paiement, documents / PDF / photos,
  e-mails / SMS / notifications, planning / calendrier, calculs automatiques, tableaux de bord.
- Les apps « variante » : un bloc pas encore construit a été retiré (ex. les fiches enfants, comme les lignes
  d'une facture). C'est écrit dans `a-tester.md`.
- Les apps « client simulé » : en plus de ce que le brief cite, elles ont les informations que l'IA
  **propose** (facultatives), comme si le client avait dit oui à toutes au miroir. Dis si une information
  proposée est absurde ou si une évidente manque : c'est un retour sur la compréhension.
- Les données de démonstration (« Intitulé 1 ») et l'apparence très simple.

## 6. Fiche de retour (une par app — à coller dans le chat)

```
App : <nom>  (runs/<dossier>)
Temps passé :
Note (0-10) — le client pourrait-il s'en servir à la place de ses tableaux ? :

Ce qui marche bien :

Problèmes (un par ligne) :
- Rôle / personne : … | Ce que j'ai fait : … | Ce qui s'est passé : … | Ce que j'attendais : … | bloquant / gênant / détail

Ce que l'app a mal compris ou oublié du brief :

Mots incompris :

Ce qui manque pour s'en servir demain :
```

## 7. Ce que je fais de tes retours

Chaque retour est classé (principe 11 d'USINE.md) puis inscrit au registre des corrections :
- **défaut de l'usine** → corrigé à la source, pour toutes les apps, puis prouvé par les juges ;
- **trou d'un juge** → le juge apprend à le voir (il n'est jamais assoupli) ;
- **bloc manquant** → compte dans la priorité du plan (N1.3 et suivants) ;
- **compréhension** → c'est le lecteur IA qui est revu, pas l'app.

Jamais de correction faite pour une seule app.
