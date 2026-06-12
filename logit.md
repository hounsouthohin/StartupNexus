Audit qualité — Recipe Manager
Score global : 5.5 / 10

BACKEND — 6.5 / 10
Ce qui est bien fait
Stack moderne et cohérente : Next.js 15, Prisma 7, Clerk v6, Zod, TypeScript strict
Architecture en couches claire : service → action → page bien respectée
Validation Zod systématique dans toutes les Server Actions avant toute écriture
Pool de connexions PostgreSQL correctement configuré (pg, max: 10, idle timeout)
Singleton Prisma en dev pour éviter les fuites lors des hot-reloads
Middleware Clerk minimal et correct avec matcher précis
Bugs et failles
Critique — IDOR (Insecure Direct Object Reference)

Dans lib/services/recipe.service.ts lignes 32–58 :


getPublicById: async (id: string) => {
  const item = await prisma.recipe.findUnique({ where: { id } })  // ← manque published: true
getPublicByIdWithRelations a le même problème. Tout visiteur anonyme qui connaît un UUID peut lire une recette privée. C'est une faille de confidentialité directe contre le brief.

Schema Prisma — datasource sans url

prisma/schema.prisma ligne 6 :


datasource db {
  provider = "postgresql"
  // manque: url = env("DATABASE_URL")
}
Prisma 7 exige ce champ explicitement — la génération du client va échouer en CI.

Cascade silencieuse

onDelete: Cascade sur Recipe → Category supprime toutes les recettes d'une catégorie sans avertissement. Le code n'offre aucune confirmation ni vérification avant une suppression de catégorie.

Pas d'unicité sur Category.name

Un utilisateur peut créer 10 catégories "Desserts". Aucun @@unique([userId, name]) dans le schema.

Pagination fantôme

Les services acceptent page et pageSize mais aucune page UI n'expose ces paramètres. L'offset est calculé mais jamais utilisé côté client.

FRONTEND — 4.5 / 10
Ce qui est bien fait
Pattern RSC + Client Component bien respecté (fetch en server, interactions en client)
useActionState correctement utilisé pour les formulaires
Design tokens CSS cohérents (variables --primary, --border, etc.)
Loading states présents sur toutes les routes dynamiques
Empty states avec CTA pertinents
Bugs fonctionnels graves
Navigation principale cassée

Dans app/components/layout/DashboardShell.tsx ligne 10 :


const NAV: NavItem[] = [
  { href: "/categories", label: "Categories" },
  // ← Recettes absentes. L'utilisateur connecté n'a aucun accès à ses recettes depuis la sidebar.
]
Le brief exige un espace privé de gestion des recettes. Il n'est pas accessible depuis la navigation.

Lignes de la table recettes non cliquables

app/recipes/page-client.tsx lignes 44–58 : chaque ligne est un <tr> sans Link. Un visiteur qui parcourt les recettes publiques ne peut pas en ouvrir une. La table est une impasse.

Composant Navigation mort

app/components/navigation.tsx existe avec Home/Recipes/Categories mais n'est importé nulle part. Code mort.

Problèmes d'UX et de cohérence
Problème	Fichier	Ligne
H1 "Recipe" en anglais	app/recipes/[id]/page-client.tsx	18
published affiché true/false au lieu de "Public/Privé"	page-client.tsx recette	55
preparationTime sans unité ("30" au lieu de "30 min")	page-client.tsx recette	37
Suppression optimiste sans rollback si l'action échoue	app/categories/page-client.tsx	18
Pas d'état de chargement pendant la suppression	page-client.tsx catégories	15
String(item.title ?? '') inutile sur des string non-nullable	partout	—
Pas de bouton "Créer" sur la page recettes pour l'utilisateur connecté	app/recipes/page-client.tsx	—
TESTS — 2 / 10
Un seul test dans tests/middleware.test.ts, structurel uniquement (vérifie que typeof middleware === 'function'). Aucun test pour :

Les services (la faille IDOR aurait été détectée ici)
Les Server Actions
Les composants clés
RÉSUMÉ POUR LA STARTUP
Critère	Note	Verdict
Architecture	7/10	Solide, bonne séparation des couches
Sécurité	3/10	IDOR critique — recettes privées accessibles publiquement
Conformité au brief	5/10	Navigation vers l'espace privé manquante, table sans clics
Qualité du code	6/10	Bien typé, quelques patterns défensifs inutiles
Tests	2/10	Quasi-absent
UX	4/10	Plusieurs blocages fonctionnels
Priorité 1 à corriger avant tout autre chose : le filtre published: true manquant dans getPublicById — c'est une faille de confidentialité directe, pas un bug cosmétique.



#####
Rapport d'évaluation — event-board
Note globale : 5.5 / 10
Backend : 6.5 / 10
Ce qui est bien fait
Authorization solide. Chaque méthode de service prend userId en premier argument et scope toutes les requêtes : where: { id, userId }. Protection IDOR correcte — un organisateur ne peut pas toucher aux données d'un autre.

Validation Zod sur toutes les Server Actions. Schémas définis dans lib/schemas.ts, appliqués avant tout appel service. Le pattern est propre.

Prisma productionisé. lib/prisma.ts utilise PrismaPg avec un pool de connexions (max 10, idle timeout 30s) et le singleton globalForPrisma pour éviter l'explosion de connexions en hot-reload. Niveau production.

Middleware Clerk propre. middleware.ts — routes publiques explicitement déclarées, toutes les autres protégées. La liste est exhaustive et correcte.

Headers de sécurité dans next.config.js — CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy. Rare pour du code auto-généré.

Health endpoint avec timeout DB. app/api/health/route.ts — Promise.race avec 3s timeout. Opérationnel.

Problèmes backend
1. Code mort — handlePrismaError jamais appelé.
lib/prisma-errors.ts gère P2002, P2025, P2003... mais les Server Actions catchent avec un message générique. Ce fichier n'est importé nulle part.

2. Logger jamais utilisé.
lib/logger.ts — pino configuré, jamais importé dans les services ni les actions.

3. Pagination sans total.
Tous les services prennent page et pageSize mais ne retournent jamais le total. L'UI ne peut pas afficher "page 2 sur 5" ni savoir quand s'arrêter.

4. Ordre de tri contre-intuitif sur les événements publics.
lib/services/event.service.ts:39 — getPublicAll trie par createdAt: 'desc' (date d'ajout). Le brief demande des "événements à venir" — ils devraient être triés par date: 'asc' (date de l'événement).

5. Duplication de types.
CreateEventInput est défini à la fois dans lib/types.ts (dérivé de Prisma) et dans lib/schemas.ts (dérivé de Zod). Deux sources de vérité pour le même concept.

6. Fuite de données dans les types.
SerializedCategory.events[] contient userId. SerializedEvent.category contient userId. Ces champs sont censés être retirés de la sérialisation publique mais remontent dans les types imbriqués.

Frontend : 4.5 / 10
Ce qui est bien fait
Architecture Server/Client correcte (page.tsx async → page-client.tsx), loading.tsx sur toutes les routes, états vides gérés, labels associés aux inputs via htmlFor.

Problèmes frontend
1. Bug critique — la liste publique n'a aucun lien.
app/events/page-client.tsx — Link est importé mais jamais utilisé. Les lignes du tableau ne sont pas cliquables. L'utilisateur ne peut pas naviguer vers /events/[id]. C'est la fonctionnalité principale de la page publique — elle est cassée.

2. Bug — le bouton retour de /events/[id] pointe vers /dashboard/events.
app/events/[id]/page-client.tsx:15 — Un visiteur non connecté qui arrive sur /events/123 ne peut pas retourner à /events. C'est une copie-colle du dashboard.

3. Dates affichées en ISO brut.
Partout : {String(item.date ?? '')} rend "2024-01-15T00:00:00.000Z". Pas de toLocaleDateString() ou de Intl.DateTimeFormat.

4. Validation Zod silencieusement ignorée côté client.
Dans app/dashboard/events/new/page-client.tsx:13-18 :


async (_prev: unknown, formData: FormData) => {
  try { await createEvent(formData); return null }  // ← swallowe le { error } retourné
  catch (e) { return (e as Error).message }
}
La Server Action createEvent retourne { error: '...' } en cas d'échec Zod — elle ne throw pas. Le wrapper client ne capture que les exceptions, donc les erreurs de validation ne sont jamais affichées. L'utilisateur soumet un formulaire invalide et... rien.

5. Erreurs de suppression ignorées.
app/dashboard/events/page-client.tsx:15-18 :


const handleDelete = async (id: string) => {
  await deleteEvent(id)
  setList(prev => prev.filter(item => item.id !== id))  // ← toujours exécuté
}
Si deleteEvent échoue côté serveur, l'item disparaît quand même de l'UI. Un refresh le fait réapparaître — comportement déroutant.

6. DashboardShell s'applique aux pages publiques.
app/layout.tsx — DashboardShell enveloppe tout. Un visiteur non connecté sur /events voit la sidebar du dashboard (vide ou avec le bouton UserButton). Le shell ne vérifie que les pages /sign-in et /sign-up, pas les routes publiques.

7. Composants UI installés mais ignorés.
components/ui/ contient Button, Input, Select, Textarea, Table... Tous les formulaires utilisent des <input> et <button> HTML bruts avec des classes Tailwind manuelles. Soit utiliser shadcn partout, soit ne pas l'installer.

8. step="any" sur la capacité.
app/dashboard/events/new/page-client.tsx:78 — Permet 2.5 participants. Le schéma Zod valide int() mais le navigateur laisse passer. Devrait être step="1".

9. Labels Franglais.
"Nouveau Event", "Modifier Event" (au lieu de "Nouvel Événement", "Modifier l'événement"). Cohérence de langue inexistante.

Synthèse pour améliorer la startup
Axe	Priorité	Action
Liens liste→détail sur /events	Critique	Ajouter <Link href={/events/${item.id}}> sur chaque ligne
Wrapper useActionState cassé	Critique	Lire le retour { error } de la Server Action, pas juste les throws
Dates formatées	Haute	new Date(item.date).toLocaleDateString('fr-FR', {...})
Delete sans feedback d'erreur	Haute	Vérifier le retour de deleteEvent avant de mettre à jour le state
Logger et handlePrismaError	Moyenne	Les brancher dans les services, ou les supprimer
Tri des événements publics	Moyenne	orderBy: { date: 'asc' } dans getPublicAll
DashboardShell sur routes publiques	Moyenne	Conditionner le shell à pathname.startsWith('/dashboard')
Pagination avec total count	Basse	Ajouter prisma.event.count({ where }) en parallèle de findMany
L'infrastructure backend est sérieuse (auth, sécurité, pooling), mais plusieurs flux utilisateur fondamentaux sont cassés côté frontend. La startup génère du code structurellement correct mais fonctionnellement incomplet — les bugs les plus graves viennent du fait que le générateur ne teste pas le flux de bout en bout.