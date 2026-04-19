# Roadmap 3.0.1 — Notes d'architecture (19 Avril 2026)

## Rappel 1 — Gestion future du code hardcodé (dette contrôlée)

### Situation actuelle
La factory génère plusieurs couches de code de manière **déterministe**, hors LLM :

| Couche | Fichier(s) | Problème futur |
|--------|-----------|----------------|
| Templates stack | `templates/*.ts`, `package.json`, `middleware.ts`... | Rigides, stack-spécifiques — pas extensibles sans toucher au JSON |
| DAL services | `lib/services/<model>.service.ts` (via `dev_pages_generator.py`) | Pattern d'ownership fixe (userId) — ne couvre pas les modèles sans userId direct |
| Types partagés | `lib/types.ts` (via `dev_types_generator.py`) | Génération basée sur les champs visibles du spec, pas du schéma réel |
| Webhook Clerk | Retiré (voir section ci-dessous) | — |

### Ce qu'il faudra décider
- **Stratégie long terme** : continuer à élargir la couche déterministe (plus de contrôle, moins de LLM) ou au contraire la réduire (moins de surface à maintenir, plus de confiance au LLM guidé par de bons standards) ?
- **Versioning des templates** : quand `@clerk/nextjs` passe en v7, ou `prisma` en v8, les templates deviennent faux. Il faudra un mécanisme de mise à jour des templates lié aux versions du stack JSON.
- **Ownership flexible dans le DAL** : aujourd'hui l'ownership assume `userId`. Cas non couverts : `authorId`, modèles enfants (Card → Board → userId), multi-tenant (orgId). Décider d'un modèle d'ownership générique ou accepter de ne générer le DAL que pour les modèles avec `userId` direct.

---

## Rappel 2 — Webhook Clerk : reporter en infra de déploiement

### Décision prise (19 Avril 2026)
Le template `app/api/webhooks/clerk/route.ts` a été **retiré** de la génération de code.

### Raison
- Importait `svix` qui n'est pas installé dans l'environnement de build → TS2307 sur 100% des projets
- Le webhook Clerk est de l'**infrastructure de déploiement**, pas du code applicatif généré
- Il nécessite des secrets Clerk (`WEBHOOK_SECRET`) non disponibles en génération
- La synchronisation Clerk → DB est un besoin réel mais doit être adressé côté **plateforme** (Clerk dashboard → endpoint de prod configuré manuellement, ou script de setup post-déploiement)

### Quand le réintroduire
Seulement si la factory adresse la phase "déploiement" (post-génération) — dans ce cas, le webhook est un template optionnel activé par une feature flag dans le brief (`"needs_user_sync": true`), pas systématique.

---

## Rappel 3 — Contrat LLM ↔ Générateurs déterministes

### Problème identifié
Les générateurs déterministes (services DAL, types) écrivent des fichiers que le LLM doit utiliser — mais le LLM ne connaît pas leur API exacte. Il invente des noms de fonctions (`getExpenses`, `getExpenseById`) au lieu d'utiliser l'objet service généré (`expenseService.findMany`).

### Solution intermédiaire appliquée (Sprint 3.0.1)
- Injection du contrat de chaque service dans le system prompt (signatures compactes)
- Entrées TS2305 et TS2322 ajoutées dans `tsc_error_catalog.py` pour correction ciblée

### Solution long terme à évaluer
Réduire la fragmentation : soit le LLM génère entièrement le DAL (guidé par des standards Qdrant stricts), soit les générateurs déterministes génèrent le DAL ET les pages qui l'utilisent (cohérence garantie). L'état actuel — DAL déterministe + pages LLM — crée un fossé de contrat.
