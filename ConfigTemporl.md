Absolument \! Félicitations, vous avez identifié la cause de votre problème d'accès à l'UI et, plus important, vous avez une configuration Docker Compose **moderne et fonctionnelle** pour Temporal avec PostgreSQL.

Le problème venait de là :

```yaml
ports:
  - "8080:8088"
```

Vous essayiez d'accéder à `localhost:8080`, mais le port du conteneur Temporal Web UI est **`8088`**. Ce mapping signifiait :

  * Accéder à l'adresse **hôte** (`localhost`) sur le port **`8080`**.
  * Ce trafic est redirigé vers le conteneur `temporal-web` sur son port **`8088`**.

Votre configuration est correcte et vous devriez y accéder via **`http://localhost:8080`**. Si l'accès ne fonctionnait pas, c'était soit :

1.  Une vieille tentative sur `http://localhost:8088` (qui n'aurait pas marché).
2.  Un problème de cache ou de pare-feu qui bloquait l'accès à `8080` après le redémarrage.

Puisque la configuration a fonctionné, voici une documentation complète basée sur vos fichiers, intégrant les bonnes pratiques actuelles.

-----

# 🚀 Guide de Configuration de l'Infrastructure Temporal avec Docker Compose

Ce document décrit la configuration de base de l'infrastructure Temporal, utilisant **PostgreSQL** comme base de données, et inclut les outils d'accompagnement **Temporal Web UI**, **n8n** (automatisation) et **Qdrant** (base de données vectorielle).

## 1\. Vue d'Ensemble de l'Architecture

L'infrastructure est déployée via Docker Compose, permettant à tous les services de communiquer sur un réseau interne (`app-network`).

| Service | Rôle | Connexion Hôte | Notes Importantes |
| :--- | :--- | :--- | :--- |
| **postgres** | Stockage persistant pour Temporal (Historique, Tâches, etc.) | N/A (Interne) | Vérification de santé (`healthcheck`) pour une dépendance stricte. |
| **temporal** | Le serveur Temporal principal (gestion du workflow) | `7233` (gRPC) | Conteneur `auto-setup` pour l'initialisation automatique du schéma. |
| **temporal-web** | Interface Utilisateur Web pour Temporal | `8080` (HTTP) | Nécessite la variable d'environnement `TEMPORAL_ADDRESS`. |
| **n8n** | Plateforme d'automatisation (facultatif) | `5678` (HTTP) | Sécurisée par Basic Auth. |
| **qdrant** | Base de données vectorielle (facultatif) | `6333` (HTTP/REST) | Utilisé pour les cas d'usage LLM/RAG (Recherche vectorielle). |

-----

## 2\. Configuration du Fichier `.env`

Le fichier `.env` stocke les informations sensibles et les paramètres de connexion.

```env
# ----------------------------------------
# 1. Base de Données (PostgreSQL)
# ----------------------------------------
POSTGRES_USER=user
POSTGRES_PASSWORD=Admin123! # ⚠️ Utilisez un mot de passe fort et unique !
POSTGRES_DB=temporal

# ----------------------------------------
# 2. Authentification n8n
# ----------------------------------------
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=Admin123! # ⚠️ Utilisez un mot de passe fort et unique !

# ----------------------------------------
# 3. Temporal (Informations non utilisées par l'image auto-setup dans ce cas)
# ----------------------------------------
TEMPORAL_USER=user
TEMPORAL_PASSWORD=Admin123! 
```

-----

## 3\. Configuration du Fichier `docker-compose.yml`

### 3.1. PostgreSQL : La Persistance

  * L'utilisation d'un **`healthcheck`** est la norme moderne pour s'assurer que le service Temporal démarre uniquement lorsque la base de données est pleinement opérationnelle.
  * Le port n'est **pas exposé** à l'extérieur (`5432:5432` est commenté) pour des raisons de sécurité, car seul le service `temporal` a besoin d'y accéder.
  * Le **volume persistant** (`postgres_data`) assure que vos données Temporal survivent aux redémarrages du conteneur.

### 3.2. Temporal Server (`temporal`) : L'Orchestrateur

  * **Image recommandée :** `temporalio/auto-setup` simplifie grandement l'installation en gérant automatiquement la création et les mises à jour du schéma PostgreSQL (ce que vous avez vu dans les logs).
  * **Connexion DB :** L'hôte est `POSTGRES_HOST=postgres`, utilisant le **nom du service** Docker Compose pour la résolution d'adresse sur le réseau interne.
  * **Dépendance Stricte :** `depends_on` avec `condition: service_healthy` garantit que Temporal attend que `postgres` soit prêt.

### 3.3. Temporal Web UI (`temporal-web`) : L'Interface

  * **Mapping de Ports (Correction Clé) :** L'UI s'exécute par défaut sur le port interne **8088**.
    ```yaml
    ports:
      - "8080:8088" # Hôte:8080 -> Conteneur:8088
    ```
    Cela rend l'UI accessible sur **`http://localhost:8080`**.
  * **Variable d'Adresse :** L'utilisation de **`TEMPORAL_ADDRESS=temporal:7233`** est la nouvelle norme (depuis mi-2024) pour que l'UI se connecte au serveur gRPC. L'ancienne variable `TEMPORAL_GRPC_ENDPOINT` est obsolète.

### 3.4. n8n et Qdrant (Services Complémentaires)

Ces services utilisent également des **volumes nommés** pour la persistance de leurs propres données et sont correctement mappés sur des ports dédiés de l'hôte :

  * **n8n :** Accessible via **`http://localhost:5678`**. Les variables de sécurité comme `N8N_BLOCK_ENV_ACCESS_IN_NODE` sont d'excellentes pratiques ajoutées.
  * **Qdrant :** Accessible via **`http://localhost:6333`** (API REST).

-----

## 4\. Démarrage de l'Infrastructure

Depuis le répertoire contenant votre `docker-compose.yml` et votre `.env` :

1.  **Démarrage :**

    ```bash
    docker compose up -d
    ```

    L'option `-d` (detached) exécute les conteneurs en arrière-plan.

2.  **Vérification de l'État :**

    ```bash
    docker compose ps
    ```

    Vérifiez que tous les services sont en `running`. Le service `temporal` prendra quelques secondes de plus, car il doit attendre que `postgres` passe à l'état `healthy`.

3.  **Accès aux Services :**

      * **Temporal Web UI :** $\rightarrow$ **`http://localhost:8080`**
      * **n8n UI :** $\rightarrow$ **`http://localhost:5678`**
      * **Qdrant API :** $\rightarrow$ **`http://localhost:6333`**

4.  **Arrêt :**

    ```bash
    docker compose down
    ```

    Cela arrête et supprime les conteneurs, mais **conserve les volumes** (et donc vos données).

5.  **Nettoyage Complet (Attention) :**

    ```bash
    docker compose down -v
    ```

    Cela supprime les conteneurs **et les volumes persistants** (vos données PostgreSQL, n8n et Qdrant seront perdues).



    # Dans le service temporal (ligne image)
image: temporalio/auto-setup:1.25.2    # au lieu de 1.21.0 → version 2025 stable + bugfixes

# Dans le service temporal-web
image: temporalio/web:2.26.1           # fixe la version pour éviter les surprises "latest"

# Ajoute cette ligne dans temporal-web (évite un warning récurrent)
environment:
  - TEMPORAL_ADDRESS=temporal:7233
  - TEMPORAL_CORS_ORIGIN=*
  - SKIP_USER_CREATION=true            # ← évite un warning inutile en dev