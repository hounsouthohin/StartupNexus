"""
scripts/migrate_zone_19_saas_senior.py

Injecte ZONE_19 dans Qdrant factory_standards.
N'efface PAS les zones existantes (ZONE_1-18 restent intactes).

ZONE_19 — Standards SaaS Senior
  Patterns de qualité production pour apps SaaS Next.js + Clerk + Prisma.
  Couvre : pages réelles, DAL, ownership, loading states, Prisma relations,
           Clerk webhook, caching sélectif, redirect auth, User model.
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_19_saas_senior.py
  docker compose exec factory-worker python scripts/migrate_zone_19_saas_senior.py --dry-run

IDEMPOTENCE : UUID déterministe (MD5 du texte) — relancer = upsert silencieux.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.embedding_provider import get_embeddings, resolve_embedding_model
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

load_dotenv(dotenv_path=ROOT / ".env")

QDRANT_URL      = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
EMBEDDING_MODEL = resolve_embedding_model(os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"))
EMBEDDINGS      = get_embeddings(EMBEDDING_MODEL)


def _uuid(text: str) -> str:
    return str(UUID(bytes=hashlib.md5(text.encode()).digest()))


def _std(zone: str, category: str, text: str) -> dict:
    return {
        "text": text.strip(),
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": zone,
            "status": "active",
            "version": "1.0",
            "category": category,
            "source": "migration-zone19-saas-senior",
            "agent_context": "dev",
        },
    }


# =============================================================================
# ZONE 19 — STANDARDS SAAS SENIOR
# =============================================================================

ZONE_19_SAAS_SENIOR = [

    # ── S1 : Page liste avec données réelles ─────────────────────────────────
    _std("19-saas-senior", "pages", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — Server Component page liste
RAISON: Une page listant des entités doit afficher les données réelles depuis Prisma. Retourner un simple <h1> sans données est interdit — l'application serait inutilisable.
DETECTION_REGEX: return\\s+<h1>[^<]+</h1>
ALTERNATIVE: Appeler prisma.model.findMany({ where: { userId } }) et mapper les résultats en JSX
EXEMPLE_INVALIDE:
  export const dynamic = 'force-dynamic';
  const InvoicesPage = () => {
    return <h1>Invoices List</h1>; // ❌ aucune donnée réelle
  };
EXEMPLE_VALIDE:
  export const dynamic = 'force-dynamic';
  import { auth } from '@clerk/nextjs/server';
  import { redirect } from 'next/navigation';
  import prisma from '@/lib/prisma';

  export default async function InvoicesPage() {
    const { userId } = await auth();
    if (!userId) redirect('/sign-in');
    const invoices = await prisma.invoice.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
    });
    return (
      <div>
        <h1>Mes factures</h1>
        {invoices.length === 0 ? (
          <p>Aucune facture pour le moment.</p>
        ) : (
          <ul>
            {invoices.map((invoice) => (
              <li key={invoice.id}>
                {invoice.amount}€ — {invoice.status}
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }
ERREUR_ATTENDUE: Page vide, utilisateur ne voit aucune donnée malgré les enregistrements en base
STATUS: active
VERSION: 1.0"""),

    # ── S2 : Page détail dynamique /[id] ─────────────────────────────────────
    _std("19-saas-senior", "pages", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — Server Component page détail [id]
RAISON: Une page détail doit récupérer l'entité par son id, vérifier l'ownership, et afficher ses champs réels. notFound() si absent ou non autorisé.
DETECTION_REGEX: params\\.id
ALTERNATIVE: findUnique + vérification userId + rendu des champs du modèle
EXEMPLE_INVALIDE:
  const PostPage = ({ params }: { params: { id: string } }) => {
    return <h1>Post {params.id}</h1>; // ❌ champ id affiché, pas le contenu
  };
EXEMPLE_VALIDE:
  export const dynamic = 'force-dynamic';
  import { auth } from '@clerk/nextjs/server';
  import { notFound } from 'next/navigation';
  import prisma from '@/lib/prisma';

  export default async function PostPage({ params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) redirect('/sign-in');
    const post = await prisma.post.findUnique({ where: { id: params.id } });
    if (!post || post.authorId !== userId) notFound();
    return (
      <article>
        <h1>{post.title}</h1>
        <p>{post.content}</p>
        <time>{post.createdAt.toLocaleDateString()}</time>
      </article>
    );
  }
ERREUR_ATTENDUE: Page blanche ou données fictives au lieu du contenu réel
STATUS: active
VERSION: 1.0"""),

    # ── S3 : Formulaire Client Component fonctionnel ──────────────────────────
    _std("19-saas-senior", "forms", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — Client Component formulaire de création
RAISON: Un formulaire doit soumettre les données à la route API correspondante via fetch, gérer les erreurs et rediriger après succès. "use client" DOIT être la ligne 1 absolue.
DETECTION_REGEX: useState.*handleSubmit
ALTERNATIVE: "use client" ligne 1, useState pour les champs, fetch vers /api/resource, router.push après succès
EXEMPLE_INVALIDE:
  export const dynamic = 'force-dynamic';
  'use client'; // ❌ use client n'est pas en ligne 1 absolue
  const NewInvoicePage = () => {
    return <h1>Create New Invoice</h1>; // ❌ formulaire absent
  };
EXEMPLE_VALIDE:
  "use client";
  import { useState } from 'react';
  import { useRouter } from 'next/navigation';

  export default function NewInvoicePage() {
    const router = useRouter();
    const [amount, setAmount] = useState('');
    const [clientId, setClientId] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      const res = await fetch('/api/invoices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: parseFloat(amount), clientId }),
      });
      if (!res.ok) { setError('Erreur lors de la création'); return; }
      router.push('/invoices');
    };

    return (
      <form onSubmit={handleSubmit}>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="Montant" required />
        <input type="text" value={clientId} onChange={(e) => setClientId(e.target.value)} placeholder="Client ID" required />
        <button type="submit">Créer la facture</button>
      </form>
    );
  }
ERREUR_ATTENDUE: Formulaire non fonctionnel, données non envoyées à l'API, pas de redirection après succès
STATUS: active
VERSION: 1.0"""),

    # ── S4 : Ownership check avant mutation ───────────────────────────────────
    _std("19-saas-senior", "security", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js API Routes — sécurité ownership PATCH/PUT/DELETE
RAISON: Tout handler qui modifie ou supprime une ressource doit vérifier que l'enregistrement appartient à l'utilisateur authentifié. Sans ce check, n'importe quel utilisateur connecté peut modifier les données d'un autre (privilege escalation horizontal).
DETECTION_REGEX: prisma\\.\\w+\\.update|prisma\\.\\w+\\.delete
ALTERNATIVE: findUnique → vérification userId === record.userId → 403 si différent → puis update/delete
EXEMPLE_INVALIDE:
  export async function PATCH(request: Request, { params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    // ❌ pas de vérification que la facture appartient à userId
    const invoice = await prisma.invoice.update({
      where: { id: params.id },
      data: { status: 'paid' },
    });
    return NextResponse.json(invoice);
  }
EXEMPLE_VALIDE:
  export async function PATCH(request: Request, { params }: { params: { id: string } }) {
    const { userId } = await auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    // ✅ ownership check obligatoire
    const existing = await prisma.invoice.findUnique({ where: { id: params.id } });
    if (!existing || existing.userId !== userId) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const body = await request.json();
    const result = updateSchema.safeParse(body);
    if (!result.success) return NextResponse.json({ error: result.error.errors }, { status: 400 });

    const invoice = await prisma.invoice.update({
      where: { id: params.id },
      data: result.data,
    });
    return NextResponse.json(invoice);
  }
ERREUR_ATTENDUE: Privilege escalation — utilisateur A peut modifier les données de l'utilisateur B
STATUS: active
VERSION: 1.0"""),

    # ── S5 : Data Access Layer (DAL) ──────────────────────────────────────────
    _std("19-saas-senior", "architecture", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js — Data Access Layer lib/services/
RAISON: Les pages ne doivent pas importer prisma directement. Encapsuler les requêtes Prisma dans lib/services/<model>.service.ts garantit la réutilisabilité, la testabilité et la cohérence de l'ownership check. Un senior isole toujours la couche données.
DETECTION_REGEX: import prisma from.*lib/prisma.*page\\.tsx
ALTERNATIVE: Créer lib/services/<model>.service.ts avec findMany/findUnique/create/update/delete. Les pages importent le service, pas prisma.
EXEMPLE_INVALIDE:
  // app/invoices/page.tsx — ❌ Prisma directement dans la page
  import prisma from '@/lib/prisma';
  export default async function InvoicesPage() {
    const invoices = await prisma.invoice.findMany({ where: { userId } });
  }
EXEMPLE_VALIDE:
  // lib/services/invoice.service.ts ✅
  import prisma from '@/lib/prisma';
  export async function getInvoicesByUser(userId: string) {
    return prisma.invoice.findMany({ where: { userId }, orderBy: { createdAt: 'desc' } });
  }
  export async function getInvoiceById(id: string, userId: string) {
    const invoice = await prisma.invoice.findUnique({ where: { id } });
    if (!invoice || invoice.userId !== userId) return null;
    return invoice;
  }
  export async function createInvoice(data: CreateInvoiceInput, userId: string) {
    return prisma.invoice.create({ data: { ...data, userId } });
  }
  export async function updateInvoice(id: string, data: Partial<CreateInvoiceInput>, userId: string) {
    const existing = await prisma.invoice.findUnique({ where: { id } });
    if (!existing || existing.userId !== userId) throw new Error('Forbidden');
    return prisma.invoice.update({ where: { id }, data });
  }

  // app/invoices/page.tsx ✅
  import { getInvoicesByUser } from '@/lib/services/invoice.service';
  export default async function InvoicesPage() {
    const invoices = await getInvoicesByUser(userId);
  }
ERREUR_ATTENDUE: Code dupliqué, ownership check oublié dans certaines routes, pages non testables isolément
STATUS: active
VERSION: 1.0"""),

    # ── S6 : Relations Prisma entre modèles ───────────────────────────────────
    _std("19-saas-senior", "database", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — relations @relation entre modèles liés
RAISON: Sans @relation explicite, Prisma ne connaît pas le lien entre les modèles. include: { client: true } est impossible, les cascades ne fonctionnent pas, et les requêtes jointes sont impossibles. Un champ clientId sans @relation est une foreign key "fantôme".
DETECTION_REGEX: \\w+Id\\s+String
ALTERNATIVE: Déclarer @relation avec fields et references sur le modèle enfant, et le champ tableau sur le modèle parent
EXEMPLE_INVALIDE:
  model Invoice {
    id       String @id @default(uuid())
    clientId String // ❌ FK sans @relation — Prisma ignore le lien
  }
EXEMPLE_VALIDE:
  model Client {
    id       String    @id @default(uuid())
    invoices Invoice[] // ✅ relation inverse déclarée
    @@index([userId])
  }
  model Invoice {
    id       String @id @default(uuid())
    client   Client @relation(fields: [clientId], references: [id]) // ✅
    clientId String
    @@index([userId])
    @@index([clientId])
  }
ERREUR_ATTENDUE: PrismaClientValidationError: Unknown field 'client' — ou jointures impossibles
STATUS: active
VERSION: 1.0"""),

    # ── S7 : Prisma indexes sur champs filtrés ────────────────────────────────
    _std("19-saas-senior", "database", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — @@index sur les champs de filtrage fréquents
RAISON: Sans index, un findMany({ where: { userId } }) fait un full table scan. Avec 10k lignes, la requête prend plusieurs secondes. Tous les champs utilisés dans where, orderBy ou join doivent avoir un index.
DETECTION_REGEX: userId\\s+String(?!.*@@index)
ALTERNATIVE: Ajouter @@index([userId]) sur tout modèle avec un champ userId ou filtré fréquemment
EXEMPLE_INVALIDE:
  model Task {
    id     String @id @default(uuid())
    userId String // ❌ pas d'index — full scan à chaque requête
  }
EXEMPLE_VALIDE:
  model Task {
    id        String   @id @default(uuid())
    userId    String
    createdAt DateTime @default(now())
    @@index([userId])           // ✅ index sur le filtre principal
    @@index([userId, createdAt]) // ✅ index composé pour tri
  }
ERREUR_ATTENDUE: Requêtes lentes en production, dégradation des performances avec la croissance des données
STATUS: active
VERSION: 1.0"""),

    # ── S8 : loading.tsx pour les pages avec fetch ───────────────────────────
    _std("19-saas-senior", "ux", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — loading.tsx Suspense automatique
RAISON: Sans loading.tsx, l'utilisateur voit une page blanche pendant le fetch Prisma. Next.js App Router utilise automatiquement loading.tsx comme Suspense boundary — le créer coûte 5 lignes et améliore drastiquement l'expérience utilisateur.
DETECTION_REGEX: prisma\\.\\w+\\.findMany|prisma\\.\\w+\\.findUnique
ALTERNATIVE: Créer loading.tsx adjacent à chaque page avec fetch Prisma, avec un skeleton ou spinner
EXEMPLE_INVALIDE:
  // ❌ app/invoices/page.tsx existe mais app/invoices/loading.tsx absent
  // L'utilisateur voit une page blanche pendant le fetch
EXEMPLE_VALIDE:
  // app/invoices/loading.tsx ✅
  export default function InvoicesLoading() {
    return (
      <div>
        <div style={{ height: '2rem', background: '#eee', marginBottom: '1rem' }} />
        <div style={{ height: '2rem', background: '#eee', marginBottom: '1rem' }} />
        <div style={{ height: '2rem', background: '#eee', marginBottom: '1rem' }} />
      </div>
    );
  }
ERREUR_ATTENDUE: Page blanche pendant le chargement, mauvaise expérience utilisateur (LCP dégradé)
STATUS: active
VERSION: 1.0"""),

    # ── S9 : Clerk Webhook — synchronisation User en base ────────────────────
    _std("19-saas-senior", "auth", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Clerk Webhooks — synchronisation utilisateur avec Prisma
RAISON: Pour une vraie SaaS, chaque utilisateur Clerk doit avoir un enregistrement en base (table User) pour stocker des données liées (profil, abonnement, paramètres). Sans webhook, la table User est toujours vide et les jointures User→données sont impossibles.
DETECTION_REGEX: clerkId|webhooks/clerk
ALTERNATIVE: Créer app/api/webhooks/clerk/route.ts qui écoute user.created/updated/deleted et synchronise la table User Prisma
EXEMPLE_INVALIDE:
  // ❌ Aucun webhook — table User jamais peuplée
  // Les requêtes prisma.user.findUnique({ where: { clerkId } }) retournent null
EXEMPLE_VALIDE:
  // app/api/webhooks/clerk/route.ts ✅
  import { Webhook } from 'svix';
  import { headers } from 'next/headers';
  import prisma from '@/lib/prisma';

  export async function POST(request: Request) {
    const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;
    if (!WEBHOOK_SECRET) return new Response('Missing secret', { status: 400 });

    const headerPayload = headers();
    const svix_id = headerPayload.get('svix-id');
    const svix_timestamp = headerPayload.get('svix-timestamp');
    const svix_signature = headerPayload.get('svix-signature');

    const body = await request.text();
    const wh = new Webhook(WEBHOOK_SECRET);
    let evt: any;
    try {
      evt = wh.verify(body, { 'svix-id': svix_id!, 'svix-timestamp': svix_timestamp!, 'svix-signature': svix_signature! });
    } catch { return new Response('Invalid signature', { status: 400 }); }

    if (evt.type === 'user.created') {
      await prisma.user.create({
        data: { clerkId: evt.data.id, email: evt.data.email_addresses[0]?.email_address ?? '' },
      });
    }
    if (evt.type === 'user.deleted') {
      await prisma.user.delete({ where: { clerkId: evt.data.id } });
    }
    return new Response('OK', { status: 200 });
  }
ERREUR_ATTENDUE: Table User vide, impossible de lier des données à un utilisateur, profil utilisateur inexistant
STATUS: active
VERSION: 1.0"""),

    # ── S10 : redirect('/sign-in') dans les pages protégées ──────────────────
    _std("19-saas-senior", "auth", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — redirect() dans les Server Components protégés
RAISON: Dans un Server Component, auth() peut retourner userId=null pour un visiteur non connecté. Retourner null ou un composant vide expose des erreurs Prisma en production. redirect('/sign-in') est la seule réponse correcte pour une page protégée.
DETECTION_REGEX: if\\s*\\(!userId\\)\\s*return\\s*null
ALTERNATIVE: import { redirect } from 'next/navigation' — redirect('/sign-in') si !userId
EXEMPLE_INVALIDE:
  export default async function DashboardPage() {
    const { userId } = await auth();
    if (!userId) return null; // ❌ page blanche — pas de redirection
    const data = await prisma.invoice.findMany({ where: { userId } }); // crash si userId null
  }
EXEMPLE_VALIDE:
  import { redirect } from 'next/navigation';
  export default async function DashboardPage() {
    const { userId } = await auth();
    if (!userId) redirect('/sign-in'); // ✅ redirection propre
    const data = await prisma.invoice.findMany({ where: { userId } });
    return <div>...</div>;
  }
ERREUR_ATTENDUE: Page blanche pour utilisateur non connecté, ou crash Prisma avec userId=null
STATUS: active
VERSION: 1.0"""),

]


# =============================================================================
# INJECTION
# =============================================================================

def _build_points(standards: list[dict]) -> list[PointStruct]:
    texts = [s["text"] for s in standards]
    vectors = EMBEDDINGS.embed_documents(texts)
    points = []
    for std, vec in zip(standards, vectors):
        uid = _uuid(std["text"])
        points.append(PointStruct(id=uid, vector=vec, payload={"text": std["text"], **std["metadata"]}))
    return points


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate ZONE_19 SaaS Senior standards to Qdrant")
    parser.add_argument("--dry-run", action="store_true", help="Liste les IDs sans injecter")
    args = parser.parse_args()

    client = QdrantClient(url=QDRANT_URL)

    all_standards = ZONE_19_SAAS_SENIOR
    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Migration ZONE_19 — {len(all_standards)} standards SaaS senior\n")

    for std in all_standards:
        uid = _uuid(std["text"])
        zone = std["metadata"]["zone"]
        cat = std["metadata"]["category"]
        preview = std["text"][:80].replace("\n", " ")
        print(f"  [{zone}] [{cat}] {uid[:8]}… — {preview}")

    if args.dry_run:
        print("\n[DRY-RUN] Aucun point injecté.")
        return

    print(f"\nGénération des embeddings pour {len(all_standards)} standards…")
    points = _build_points(all_standards)

    print(f"Upsert de {len(points)} points dans '{COLLECTION_NAME}'…")
    client.upsert(collection_name=COLLECTION_NAME, points=points)

    info = client.get_collection(COLLECTION_NAME)
    print(f"\n✅ Migration ZONE_19 terminée — collection contient maintenant {info.points_count} standards.")


if __name__ == "__main__":
    main()
