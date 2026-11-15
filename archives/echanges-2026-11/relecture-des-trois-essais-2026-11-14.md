# Relecture des trois essais jetables

## Dossier 1.1 — La boîte de l'agent

**VERDICT : OK AVEC CORRECTIONS**

**BLOQUANT**

Aucun. La conception est saine, les sabotages sont écrits d'avance, et tout se défait d'une commande.

**À CORRIGER**

1. **Le réseau interne ne coupe pas l'accès à l'hôte.** Selon la documentation de Docker, sur un réseau `--internal`, la communication avec l'adresse de la passerelle, et donc avec les services de l'hôte configurés en conséquence, reste possible. Ici, « l'hôte » est la machine virtuelle de WSL, partagée par toutes les distributions. Un service qui écoute sur toutes les adresses dans cette machine (l'ancienne Ubuntu, un serveur de développement) devient joignable depuis la boîte. Le sabotage n° 4 ne teste que le port 5432 et Windows. **Correction :** étendre le sabotage n° 4 à un balayage des ports de l'adresse de passerelle et de l'adresse de la machine virtuelle. Ajouter dans `usine` une règle de pare-feu qui refuse tout trafic venant du sous-réseau de la boîte vers l'hôte ; la base est un conteneur, elle n'en a pas besoin. Source : [Docker, `network create`](https://docs.docker.com/engine/reference/commandline/network_create).

2. **La fuite par le DNS.** Un avis de sécurité de Moby signale que les réseaux internes pouvaient transmettre des requêtes DNS à un serveur de noms externe. C'est une voie de sortie classique pour faire fuir des données. **Correction :** ajouter un sabotage « résoudre un nom externe » (par exemple `registry.npmjs.org`), qui doit échouer, et vérifier que la version figée de Docker Engine contient le correctif. Source : [avis GHSA-mq39-4gv4-mvpx](https://github.com/advisories/GHSA-mq39-4gv4-mvpx).

3. **Le socket de Docker manque dans les sabotages.** C'est l'évasion la plus courante : un conteneur qui voit `/var/run/docker.sock` contrôle tout le moteur. **Correction :** ajouter un sabotage n° 9, « joindre le socket Docker », qui doit échouer. mini-swe-agent passe par `docker exec` depuis l'extérieur : la boîte n'a jamais besoin du socket.

4. **Chromium dans la boîte va manquer de mémoire partagée.** La documentation de Playwright indique qu'utiliser `--ipc=host` est recommandé avec Chromium, faute de quoi il peut manquer de mémoire et planter. Mais `--ipc=host` affaiblit l'isolement. **Correction :** ne pas prendre `--ipc=host` ; utiliser plutôt une taille de `/dev/shm` suffisante (`--shm-size`), puisque Playwright recommande `--ipc=host`, et une taille `--shm-size` adaptée est l'alternative quand le partage avec l'hôte n'est pas acceptable. Ajouter aussi `--init` : le drapeau `--init` est recommandé pour éviter le traitement spécial du processus n° 1, cause fréquente de processus zombies. Source : [Playwright, Docker](https://playwright.dev/dotnet/docs/docker).

5. **La construction peut échouer faute de réseau, pour une mauvaise raison.** Si le squelette utilise `next/font/google`, `next build` télécharge la police pendant la construction. Sans réseau, la construction échoue sur l'impossibilité de joindre fonts.googleapis.com. Le témoin « construire l'app » échouerait, et l'essai conclurait à tort que la boîte ne tient pas. **Correction :** vérifier le squelette avant l'essai ; utiliser des polices locales (`next/font/local`) intégrées à l'image. Désactiver aussi la télémétrie de Next.js (`NEXT_TELEMETRY_DISABLED=1`). Source : [wiki NixOS, Node.js](https://wiki.nixos.org/wiki/Node).

6. **Le système de fichiers en lecture seule casse des écritures invisibles.** npm, Next.js et Playwright écrivent dans `HOME`, dans `~/.cache` et parfois dans `node_modules/.cache`. Avec `--read-only` et `node_modules` en lecture seule, les témoins échoueront pour une raison sans rapport avec la sécurité. **Correction :** pointer `HOME` et les caches vers le `tmpfs`, et fixer `PLAYWRIGHT_BROWSERS_PATH` vers les navigateurs de l'image. Tester ces témoins **avant** les sabotages.

7. **Le seuil « créer + détruire < 10 s » mesure mal la base.** Un conteneur PostgreSQL démarre vite, mais n'accepte pas tout de suite les connexions. **Correction :** mesurer jusqu'à ce que `pg_isready` réponde, pas jusqu'au démarrage du conteneur.

**SUGGESTIONS**

1. **Question 1 (base jetable par tâche).** C'est le bon choix : isolement complet, sans autre base joignable. Pour gagner du temps : une image PostgreSQL avec les données de démonstration déjà chargées.
2. **Question 2 (sans root, remappage).** Pas nécessaire pour cet essai : utilisateur non administrateur, privilèges retirés et `no-new-privileges` forment une base raisonnable. Attention si vous passez au mode sans root plus tard : les plafonds de mémoire et de processeur y dépendent de la délégation des cgroups v2, à vérifier sous WSL.
3. **Question 4 (deux moteurs Docker).** Les pièges connus sont ceux du dossier (intégration WSL de Docker Desktop, mémoire partagée), plus les conflits de ports si les deux moteurs publient le même. La boîte ne publie aucun port : pas de conflit attendu.
4. **Noter la taille du disque virtuel** de `usine` à la fin. Il grossit et ne rétrécit pas tout seul.

**NON VÉRIFIÉ**

- **`wsl --install --name`.** La documentation de Microsoft confirme que le nom par défaut peut être remplacé par `wsl.exe --install <distro> --name <n>`, pour les distributions au format moderne, à partir de WSL 2.4.4. Je n'ai pas vérifié qu'Ubuntu-24.04 est livrée dans ce format ; le repli par export puis import reste valable.
- La version de Docker Engine qui corrige la fuite DNS.
- Le comportement du bac à sable de Chromium avec `--cap-drop ALL` et un utilisateur non administrateur ; le témoin « ouvrir l'app dans Chromium » le dira.
- La délégation des cgroups v2 sous WSL.

## Dossier 1.2 — Le moteur par la boîte aux lettres

**VERDICT : À REVOIR**

**BLOQUANT**

1. **Le montage contredit les conditions d'utilisation de l'abonnement.** Le dossier fait d'une session Claude Code de l'abonnement « le modèle de langage derrière » mini-swe-agent, un agent tiers. Or Anthropic réserve l'authentification de ces abonnements : l'authentification OAuth des formules Free, Pro et Max est destinée exclusivement à Claude Code et Claude.ai ; l'utiliser dans tout autre produit, outil ou service, y compris l'Agent SDK, n'est pas permis. Le relais par fichiers évite le refus technique des serveurs, mais pas la règle : c'est précisément un outil tiers alimenté par l'abonnement. Par ailleurs, Anthropic se réserve le droit d'agir sans préavis, et les limites de Pro et Max sont pensées pour un usage individuel ordinaire.
   - **Pourquoi c'est grave :** le risque n'est pas l'essai, c'est le compte. Le perdre, c'est perdre aussi l'outil qui construit l'usine elle-même.
   - **Correction :** inverser les options. L'option 2 (Claude Code lui-même comme agent constructeur, lancé par l'orchestrateur) devient la voie principale tant qu'il n'y a pas de budget d'API ; mini-swe-agent attend ce budget. L'adaptateur `ModeleBoite` reste utile autrement (voir les suggestions).
   - **Sources :** [The Register](https://www.theregister.com/2026/02/20/anthropic_clarifies_ban_third_party_claude_access), [WinBuzzer](https://winbuzzer.com/2026/02/19/anthropic-bans-claude-subscription-oauth-in-third-party-apps-xcxwbn/), [analyse de yage.ai](https://yage.ai/share/claude-code-subscription-not-a-developer-credential-en-20260321.html).
   - La boîte aux lettres des lecteurs pose la même question, à un degré moindre : le travail y est fait par des agents Claude Code avec leurs propres outils. Elle mérite son propre examen.

**À CORRIGER** (si l'essai est maintenu, ou pour l'option 2)

1. **Question 1 : le coût en quota est plus élevé qu'un appel d'API.** Chaque étape lance un agent neuf qui fait au moins trois tours internes : lire la demande, écrire la réponse, terminer. Il paie à chaque fois les consignes de Claude Code, puis relit toute la conversation, qui grossit. Le total croît à peu près comme le carré du nombre d'étapes, multiplié par deux ou trois par rapport à une boucle d'API. **Correction :** mesurer trois étapes à vide avant l'essai, et écrire d'avance un arrêt sur le quota (« au-delà de X % après 10 étapes, on arrête »).
2. **La lecture d'une longue conversation.** L'outil de lecture de Claude Code lit par défaut un nombre limité de lignes, et peut couper les lignes très longues (à vérifier). La demande témoin vérifie la longueur des lignes, pas le nombre de lignes. **Correction :** une seconde demande témoin de plus de 2 000 lignes, dont le répondeur doit recopier la dernière.
3. **Le répondeur n'est pas un modèle brut.** C'est un agent avec ses propres consignes de sécurité : il peut commenter, refuser une commande qui lui paraît risquée, ou s'écarter du format. **Correction :** compter ces écarts à part des erreurs de format, et les regarder un par un.
4. **Le test caché peut rater une fuite.** Il compare le nombre affiché au nombre permis, mais une page peut afficher le bon nombre tout en envoyant au navigateur des fiches cachées, filtrées ensuite côté client. **Correction :** ajouter une vérification : le nom d'une fiche cachée n'apparaît ni dans le HTML, ni dans les données envoyées au navigateur.
5. **Le « cœur » de l'app A n'est pas défini.** A n'a pas été posée par l'assembleur. **Correction :** écrire la liste exacte des chemins montés en lecture seule pour A (`zenstack/`, `package*.json`, règles, configuration).

**SUGGESTIONS**

1. **Garder `ModeleBoite` comme outil d'enregistrement et de rejeu.** Des réponses enregistrées une fois, rejouées par leur `DeterministicModel`, permettent de tester la boucle, la boîte et l'orchestrateur à 0 $, de façon reproductible.
2. **Question 4 (format texte ou appels d'outils).** Avec une boîte aux lettres, le format texte est le bon choix. Avec l'API plus tard, il faudra suivre la recommandation des auteurs, que je n'ai pas vérifiée.
3. **L'option de comparaison avec une session Claude Code ordinaire** est utile : elle sert de référence de qualité.

**NON VÉRIFIÉ**

- La position officielle d'Anthropic sur ce montage précis (un relais par fichiers) : je cite des comptes rendus de la page officielle, pas la page elle-même.
- La coupure des longues lignes par l'outil de lecture de Claude Code.
- La consommation réelle de quota par étape, et l'effet de la mise en cache entre deux agents neufs.

## Dossier 1.3 — Le moteur de parcours

**VERDICT : OK AVEC CORRECTIONS**

**BLOQUANT**

Aucun. Les corrections ci-dessous changent la manière de juger les interdictions et de classer les échecs ; elles se font avant de lancer l'essai.

**À CORRIGER**

1. **« Tenter par l'adresse directe » ne marche pas pour une action.** Dans Next.js, une Server Action s'exécute comme une requête POST vers la page qui l'appelle, et les références d'action sont chiffrées à la construction. Il n'existe pas d'adresse générique de l'action « confirmer ». Une interdiction d'action serait donc soit non jugée, soit jugée à tort. **Correction :** capturer la requête POST du jumeau permis pendant son parcours, puis la rejouer avec la session du rôle interdit ; la base ne doit pas changer. C'est générique, sans code propre à une app. L'adresse directe reste valable pour les **pages** (voir une fiche). Source : [Next.js, Server Actions](https://nextjs.org/docs/app/guides/server-actions).

2. **La recherche par nom est partielle par défaut.** Pour `getByRole`, la correspondance du nom ignore la casse et cherche une sous-chaîne par défaut ; l'option `exact` contrôle ce comportement. « Confirmer » trouverait aussi « Confirmer la suppression » : fausse ambiguïté, ou pire, clic sur le mauvais bouton. **Correction :** `exact: true` partout, ou une expression régulière ancrée. Source : [Playwright, getByRole](https://playwright.dev/docs/api/class-framelocator).

3. **Question 2 : l'erreur de Playwright ne suffit pas à classer les échecs.** Un élément absent, pas encore affiché, caché derrière un menu ou une pagination, désactivé ou recouvert : tous finissent par la même erreur de délai. « Introuvable » se confondrait avec « environnement ». Seul le mode strict donne une erreur distincte et fiable (plusieurs éléments). **Correction :** une fois la page stable, compter les éléments. Zéro : introuvable. Plus d'un : ambigu. Un seul mais inutilisable (désactivé, recouvert) : une classe à part. Ne classer « environnement » que les échecs de chargement et de navigateur.

4. **La base neuve par parcours, avec l'app qui tourne.** Copier une base modèle exige qu'aucune autre session n'y soit connectée, et l'app en marche garde ses connexions ouvertes. Changer de base à chaque parcours imposerait de redémarrer l'app. **Correction :** décider avant l'essai entre trois options : redémarrer l'app à chaque parcours (lent), remettre les données à zéro dans la même base (rapide), ou une instance de l'app par base. Source : documentation de PostgreSQL sur `CREATE DATABASE … TEMPLATE`, non relue ici.

5. **Question 1 : il manque de quoi trouver l'objet.** Pour trouver « le devis D-1 », le parcours doit dire :
   - comment le reconnaître à l'écran : un libellé visible et unique, posé exprès dans les données de départ ;
   - comment y arriver : par les noms accessibles (le lien du menu porte le libellé de la fiche), pas par une adresse propre à une app ;
   - quelle personne précise joue l'acteur (`_1` ou `_2`), pour les règles « les siennes » ;
   - la correspondance entre le code d'état et le libellé affiché.

6. **L'horloge figée ne fige que le navigateur.** Le serveur de Next.js garde l'heure réelle. **Correction :** fixer le fuseau du serveur, et éviter les parcours qui dépendent de la date dans cet essai.

**SUGGESTIONS**

1. **Question 3 (le juge partage l'erreur de l'usine).** Oui, en partie. Une erreur du calculateur produirait à la fois de mauvaises règles et de mauvais parcours, qui s'accorderaient. Les parades existent ailleurs (matrice validée par le client, banc du calculateur). Pour l'essai, ajouter trois à cinq parcours écrits à la main pour B, depuis les phrases du miroir, comme contrôle croisé.
2. **Question 4 (le jumeau permis).** Il suffit pour distinguer « absent » de « mal nommé ». Il manque un cas : le bouton visible mais désactivé pour le rôle interdit. C'est une affordance trompeuse, pas une violation, sauf si la requête rejouée réussit.
3. **Question 5 (les seuils).** B mélange les pièces de l'usine et quatre écrans d'agent : 90 % pourrait venir surtout des pièces de l'usine. Donner le taux séparément pour chaque origine. Préciser que « ≤ 2 min » vaut pour un passage, pas pour les trois.
4. **Enregistrer une trace Playwright et une capture d'écran à chaque échec**, pour pouvoir le relire.

**NON VÉRIFIÉ**

- La contrainte exacte de PostgreSQL sur les connexions à la base modèle (connue, mais pas relue à la source ici).
- La façon dont les pages de connexion de A et A0 exposent l'identifiant de la personne (bouton, liste déroulante) ; l'essai le mesurera.
- Le comportement de Playwright face à un élément présent mais désactivé ou recouvert, au-delà de l'erreur de délai.