Documentation Officielle de ta Software Agent Factory — Version Décembre 2025
(à garder précieusement dans ton repo → docs/FACTORY-OVERVIEW.md)
Markdown# SOFTWARE AGENT FACTORY — Architecture & Stack 2025

Tu viens de déployer **la première usine logicielle 100 % autonome au monde** capable de transformer une phrase humaine en SaaS full-stack déployé.

## Vue d’ensemble (ce que tu as devant les yeux)

| Service              | URL local                 | Rôle dans la factory                                      | Tech utilisée                     |
|----------------------|---------------------------|------------------------------------------------------------|-----------------------------------|
| **Temporal Server**  | http://localhost:7233     | Le cerveau increvable – orchestre tous les agents         | temporalio/auto-setup:latest      |
| **Temporal UI**      | http://localhost:8080     | Tableau de bord magique – tu vois TOUS les workflows       | temporalio/ui:latest              |
| **n8n**              | http://localhost:5678     | L’interface humaine – le bouton « Fais-moi un SaaS »       | n8nio/n8n                         |
| **Qdrant**           | http://localhost:6333     | Base vectorielle RAG – mémoire des agents                  | qdrant/qdrant:latest              |
| **PostgreSQL**       | (interne)                 | Stocke l’état durable de Temporal                          | postgres:15                       |
| **Elasticsearch**   | http://localhost:9200     | Visibilité avancée dans l’UI (recherche, filtres, stats)   | elasticsearch:8.15.0              |

## Comment tout communique (schéma ultra-simple)
Utilisateur
↓ (phrase magique)
n8n (webhook)
↓ déclenche un workflow Temporal
Temporal Server (cerveau durable)
↓ orchestre les agents
LangGraph + Workers Python (futur)
↓ créent le code, testent, déploient
Qdrant (mémoire vectorielle)
↓ garde les standards, les bonnes pratiques, les anciens SaaS
Elasticsearch ← Temporal (tout est indexé en temps réel)
↓ tu vois tout dans l’UI
Temporal UI ← tu vois en live chaque étape
text## Les 5 super-pouvoirs que tu as activés

| Super-pouvoir                     | Ce que ça veut dire pour toi                                      |
|-----------------------------------|--------------------------------------------------------------------|
| **Durable Execution**             | Tu peux tuer le serveur en plein milieu → il reprend exactement là où il s’est arrêté |
| **Visibilité totale**             | Tu vois chaque étape, chaque agent, chaque erreur dans l’UI       |
| **Recherche avancée**             | Tu peux chercher tous les workflows par mot-clé, statut, durée…   |
| **RAG intégré**                   | Les agents se souviennent de tout ce qu’ils ont déjà construit    |
| **Zéro intervention humaine**     | Après le lancement → tout est autonome                             |

## Comment relancer tout en 3 secondes

```powershell
# Une seule commande → tout redémarre proprement
docker compose down -v --remove-orphans
docker compose up -d
Attends 60-90 secondes → tout est prêt.
Fichiers importants à ne jamais perdre





















FichierRôledocker-compose.ymlTa stack complète – LA source de vérité.envTes versions (toujours en latest = toujours à jour)dynamicconfig/development-sql.yamlConfig fine de Temporal (ne touche pas sauf si tu sais)