.
les 9 types d'apps que cette stack peut produire :

Code	Type	Exemples
A	CRUD SaaS simple (périmètre actuel)	project-hub, contact-crm, leave-manager, task manager
B	Multi-tenant SaaS	Notion, Slack, Figma clone — workspaces/organisations
C	Marketplace / Platform	Etsy, Airbnb, Upwork clone — deux côtés
D	Blog / CMS	Medium clone, documentation, publishing workflow
E	E-commerce	Boutique, catalogue, panier, commandes
F	Social / Communauté	Feed, likes, follows, commentaires, notifications
G	Booking / Calendrier	Prise de RDV, disponibilités, créneaux
H	Dashboard / Analytics	Métriques, agrégations, séries temporelles
I	Workflow / Approbation	Processus RH, validation commandes, review content
J	Gestion de fichiers/documents	Uploads, versioning, permissions fichiers
Audit des limites déterministes
L1 — Omit<PrismaType, K> ne fonctionne pas avec Prisma 7
Fichier : dev_types_generator.py ligne 208

Impact : SerializedXxx = { createdAt: string } seulement — id, content, tous les autres champs manquants

Apps bloquées : TOUS — bloque le BUILD dès qu'un modèle a un champ DateTime

Fix : Générer un type explicite en énumérant tous les champs scalaires (à faire maintenant)

L2 — Owner = toujours userId, un seul propriétaire par modèle
Fichier : dev_service_generator.py ligne 67 — _resolve_owner(model) retourne userId par défaut

Ce que ça produit :


getAll: async (userId: string) => prisma.project.findMany({ where: { userId } })
Problème : en Multi-tenant, le modèle appartient à un organizationId ou workspaceId, pas à userId. En Marketplace, un Product appartient à un sellerId, pas un userId générique. En Social, un Post peut avoir authorId + communityId.

Apps bloquées : B (multi-tenant), C (marketplace), G (booking team-based)

Fix : ProjectSpec doit exposer owner_type: "user" | "organization" | "public" + owner_field: string — le générateur lit ces champs

L3 — Aucun modèle public (sans owner)
Fichier : dev_service_generator.py ligne 103 — where: { userId } toujours injecté

Problème : Un catalogue de produits, un article de blog publié, une fiche vendeur — ces modèles se lisent sans authentification. Actuellement le service force un userId qui n'existe pas → résultats vides ou erreur runtime.

Apps bloquées : C (listings publics), D (articles publiés), E (catalogue produits)

Fix : Détecter quand resolved_owner() retourne null (modèle public) → générer getAll(): Promise<SerializedXxx[]> sans where

L4 — getAll sans pagination
Fichier : dev_service_generator.py ligne 104

Ce que ça produit :


const items = await prisma.project.findMany({ where: { userId } })  // ALL records
Problème : 1 000 produits e-commerce ? 50 000 articles de blog ? La requête charge tout en mémoire, le serveur s'effondre.

Apps bloquées : D, E, F, H, I — toute app au-delà de ~100 enregistrements

Fix : Ajouter take? et skip? optionnels + retourner { data: SerializedXxx[], total: number }

L5 — getAll sans tri
Fichier : dev_service_generator.py ligne 104 — aucun orderBy

Problème : Un feed social non trié par createdAt DESC est inutilisable. Un catalogue produits sans orderBy: { price: 'asc' } est incohérent.

Apps bloquées : D (articles par date), E (produits par prix), F (feed chronologique), G (créneaux triés)

Fix : Détecter les champs createdAt/updatedAt → orderBy: { createdAt: 'desc' } par défaut ; rendre configurable dans ProjectSpec

L6 — getAll sans filtrage ni recherche
Fichier : dev_service_generator.py ligne 104

Problème : Impossible de faire getByStatus('PENDING'), searchByName('claude'), getByCategory('tech') — le service ne génère aucune méthode de filtrage.

Apps bloquées : C (filtrer par catégorie), D (filtrer par tag/status), E (filtrer par prix), F (filtrer par type de post), I (filtrer par statut d'approbation)

Fix : Détecter les champs status, category, type dans le schéma → générer getByStatus(userId, status) ou une méthode générique findMany(userId, where?)

L7 — Relations à un seul niveau (include: { relation: true })
Fichier : dev_service_generator.py ligne 115-122

Ce que ça produit :


prisma.project.findMany({ include: { tasks: true } })  // ← tasks sans leurs comments
Problème : Pour afficher Project → Tasks → Comments, un seul niveau ne suffit pas. Pour Order → OrderItems → Product, il faut include: { items: { include: { product: true } } }.

Apps bloquées : B (workspace → channels → messages), C (order → items → products), D (article → sections → blocks), E idem

Fix : ProjectSpec expose include_depth: number ou des relations imbriquées explicites → le générateur construit le bloc include en récursif

L8 — Enums Prisma mappés en string
Fichier : dev_types_generator.py ligne 63 — _PRISMA_TO_TS.get(base, "string" if base[0].isupper()...)

Ce que ça produit pour Status enum :


// Devrait être :  status: Status  (depuis @prisma/client)
// Est généré :    status: string  ← TypeScript ne valide plus les valeurs
Problème : status: "APPROVD" (faute de frappe) passe TypeScript. L'enum est la protection contre ça.

Apps bloquées : I (PENDING/APPROVED/REJECTED), E (PENDING/PAID/SHIPPED/DELIVERED), D (DRAFT/PUBLISHED/ARCHIVED), F (PUBLIC/PRIVATE/FOLLOWERS_ONLY)

Fix : Détecter les Enums depuis ProjectSpec → import type { Status } from '@prisma/client' → status: Status dans les types

L9 — Soft delete (deletedAt) non géré
Fichier : dev_types_generator.py ligne 40 — "deletedat" dans _AUTO_FIELDS (exclu des inputs) mais dev_service_generator.py n'ajoute jamais where: { deletedAt: null }

Ce que ça produit :


getAll: async (userId) => prisma.contact.findMany({ where: { userId } })
// retourne AUSSI les contacts supprimés
Apps bloquées : C (contacts CRM supprimés), D (articles archivés), E (commandes annulées), F (posts supprimés), J (documents supprimés)

Fix : Détecter deletedAt DateTime? dans le schéma → ajouter automatiquement deletedAt: null au where

L10 — Decimal non sérialisé (comme DateTime)
Fichier : dev_types_generator.py ligne 31 — "Decimal": "number" + dev_service_generator.py — _serialize ne touche pas les Decimal

Problème : Prisma retourne Decimal (objet Prisma custom), pas un number JavaScript. .toNumber() est nécessaire. Sans sérialisation, JSON.stringify échoue en production et le Client Component plante.

Apps bloquées : E (prix produits), H (métriques financières), tout SaaS avec montants exacts

Fix : Decimal dans _PRISMA_TO_TS → number dans le type ET _serialize ajoute field: item.field.toNumber() comme pour DateTime

L11 — Relations many-to-many non supportées
Fichier : dev_service_generator.py ligne 47 — _relation_fields détecte uniquement @relation explicite

Problème : Les relations implicites many-to-many (Post ↔ Tag via table pivot auto-générée par Prisma) n'ont pas de @relation dans les champs — le générateur les ignore complètement.

Apps bloquées : D (articles ↔ tags/catégories), C (produits ↔ tags), F (users ↔ groups), E (produits ↔ promotions)

Fix : Détecter les champs de type tableau (Tag[], Category[]) sans @relation → les inclure dans getAllWithRelations

L12 — Champs Json inutilisables
Fichier : dev_types_generator.py ligne 34 — "Json": "unknown"

Problème : content: unknown force des casts partout. Le LLM ne sait pas comment typer/utiliser ce champ → improvise → erreurs TypeScript.

Apps bloquées : D (rich text en JSON), H (event metadata), J (document content), tout app avec config flexible

Fix : Accepter un champ optionnel json_type dans ProjectSpec (json_type: "Record<string, unknown>" ou une interface nommée) → le générateur l'utilise

L13 — Pas de méthodes d'agrégation (count, sum, avg)
Fichier : dev_service_generator.py — aucun prisma.model.aggregate() généré

Problème : Un dashboard avec "42 projets actifs", "€12,500 de CA ce mois" ou "85 nouveaux utilisateurs" nécessite des agrégations. Le LLM les improvise dans les Server Components → erreurs, requêtes N+1.

Apps bloquées : H (ENTIÈREMENT), E (totaux commandes), F (compteurs likes/follows), I (taux d'approbation)

Fix : Détecter les modèles marqués analytics: true dans ProjectSpec → générer count(userId), aggregate(userId, field)

L14 — getById uniquement par id, pas par slug
Fichier : dev_service_generator.py ligne 108 — where: { id, userId } seulement

Problème : Un blog, un portfolio, un e-commerce veulent des URLs /articles/mon-titre-article — slug unique, SEO-friendly. Aucune méthode générée pour ça.

Apps bloquées : D (blog), E (produits), C (profils vendeurs)

Fix : Détecter les champs nommés slug avec @unique → générer getBySlug(slug: string): Promise<SerializedXxx | null>

L15 — create atomique (multi-modèles) non généré
Fichier : dev_service_generator.py ligne 126 — un seul prisma.model.create()

Problème : Créer une Order avec ses OrderItems doit être atomique ($transaction). Créer un Workspace avec son WorkspaceMember (rôle owner) est toujours couplé. Le générateur ne gère qu'un modèle à la fois.

Apps bloquées : E (commandes + items), B (workspace + member owner), G (booking + confirmation)

Fix : ProjectSpec expose des transactions: [{ trigger: "createOrder", models: ["Order", "OrderItem"] }] → générateur crée une méthode createWithItems(userId, data, items) avec $transaction

L16 — Actions 100% LLM (le plus critique après L1)
Fichier : aucun — les app/*/actions.ts sont entièrement générés par le LLM

Ce que le LLM produit avec trop de variance :


// ❌ Run 1 : manque auth guard
export async function createProject(formData: FormData) {
  const data = CreateProjectSchema.parse(Object.fromEntries(formData))
  await prisma.project.create({ data })  // ← accès direct Prisma, bypass service
}

// ❌ Run 2 : mauvais schema
export async function createProject(formData: FormData) {
  const { userId } = await auth()
  const data = ProjectSchema.parse(...)  // ← ProjectSchema n'existe pas
}

// ❌ Run 3 : manque revalidatePath
export async function deleteProject(id: string) {
  const { userId } = await auth()
  await projectService.delete(userId, id)
  // ← pas de revalidatePath → UI ne se met jamais à jour
}
Pourtant une Server Action CRUD est 100% dérivable de ProjectSpec :


// createProject → toujours la même structure :
'use server'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { projectService } from '@/lib/services/project.service'
import { CreateProjectSchema } from '@/lib/schemas'

export async function createProject(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = CreateProjectSchema.parse(Object.fromEntries(formData))
  await projectService.create(userId, validated)
  revalidatePath('/projects')  // ← dérivé du path de la page liste
}
Tout vient de ProjectSpec : quel service, quel schema, quel revalidatePath.

Apps bloquées : TOUS — les mutations sont cassées ou non sécurisées dans ~40% des runs

Fix : Créer dev_actions_generator.py qui génère les 3 CRUD actions (create, update, delete) par modèle. Le LLM garde uniquement les actions métier complexes (workflow, notifications, $transaction).

Récapitulatif — priorités par niveau d'évolution
#	Limite	Apps débloquées	Priorité
L1	Bug Omit<PrismaType>	TOUS	🔴 P0 — à fixer maintenant
L16	Actions 100% LLM	TOUS	🔴 P0 — bloque la fiabilité
L10	Decimal non sérialisé	E, H	🟠 P1 — prochain run e-commerce
L8	Enums → string	D, E, I	🟠 P1 — perte typage critique
L4	Pas de pagination	D, E, F, H	🟠 P1 — crash en prod
L3	Pas de modèle public	C, D, E	🟠 P1 — bloque marketplace/blog
L9	Soft delete ignoré	C, D, E, F	🟡 P2 — bug silencieux
L5	Pas de tri	D, E, F, G	🟡 P2 — UX cassée
L2	Owner = userId hardcodé	B, C, G	🟡 P2 — bloque multi-tenant
L7	Relations 1 niveau	B, C, D, E	🟡 P2 — données incomplètes
L11	Many-to-many ignoré	C, D, F	🟡 P2
L6	Pas de filtrage	C, D, E, F, I	🟡 P2
L13	Pas d'agrégations	H entier	🟡 P2
L14	Pas de getBySlug	C, D, E	🟡 P2
L12	Json → unknown	D, H, J	🟢 P3
L15	Create atomique	B, E, G	🟢 P3
Maintenant on fixe L1 ?