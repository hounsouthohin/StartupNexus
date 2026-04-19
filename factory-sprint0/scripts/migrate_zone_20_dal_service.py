"""
scripts/migrate_zone_20_dal_service.py

Injecte ZONE_20 dans Qdrant factory_standards.
N'efface PAS les zones existantes (ZONE_1-19 restent intactes).

ZONE_20 — Service DAL Pattern (Option B)
  Standards pour la génération des lib/services/<model>.service.ts par le LLM.
  Couvre : structure de l'objet service, ownership check userId/authorId,
           modèles enfants sans userId direct, import pattern dans les pages,
           nommage fichier (kebab) et objet (camelCase + Service).
  agent_context: dev

COMMANDE :
  cd factory-sprint0
  docker compose exec factory-worker python scripts/migrate_zone_20_dal_service.py
  docker compose exec factory-worker python scripts/migrate_zone_20_dal_service.py --dry-run

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
            "source": "migration-zone20-dal-service",
            "agent_context": "dev",
        },
    }


# =============================================================================
# ZONE 20 — SERVICE DAL PATTERN
# =============================================================================

ZONE_20_DAL_SERVICE = [

    # ── S1 : Structure de base du service DAL ────────────────────────────────
    _std("20-dal-service", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/services/<model>.service.ts
RAISON: Centraliser tous les accès Prisma dans un objet service garantit l'ownership check systématique et fournit un contrat stable que les pages peuvent importer. Sans DAL, le LLM oublie les ownership checks dans certaines routes.
NOMMAGE: Modèle Post → fichier post.service.ts → objet postService. Modèle InvoiceItem → fichier invoice-item.service.ts → objet invoiceItemService (kebab pour le fichier, camelCase pour l'objet).
DETECTION_REGEX: export\\s+function\\s+get[A-Z]|export\\s+async\\s+function\\s+get[A-Z]
ALTERNATIVE: Exporter un objet unique avec méthodes (findMany, findUnique, create, update, delete)
EXEMPLE_INVALIDE:
  export async function getExpenses(userId: string) { ... }
  export async function getExpenseById(id: string) { ... }
  export async function createExpense(data: any) { ... }
EXEMPLE_VALIDE:
  import prisma from '@/lib/prisma'

  export const expenseService = {
    findMany: (userId: string) =>
      prisma.expense.findMany({ where: { userId }, orderBy: { createdAt: 'desc' } }),

    findUnique: async (id: string, userId: string) => {
      const r = await prisma.expense.findUnique({ where: { id } })
      if (!r || r.userId !== userId) return null
      return r
    },

    create: (data: { amount: number; category: string; description: string; date: string }, userId: string) =>
      prisma.expense.create({ data: { ...data, userId } }),

    update: async (id: string, data: Partial<{ amount: number; category: string }>, userId: string) => {
      const r = await prisma.expense.findUnique({ where: { id } })
      if (!r || r.userId !== userId) throw new Error('Forbidden')
      return prisma.expense.update({ where: { id }, data })
    },

    delete: async (id: string, userId: string) => {
      const r = await prisma.expense.findUnique({ where: { id } })
      if (!r || r.userId !== userId) throw new Error('Forbidden')
      await prisma.expense.delete({ where: { id } })
    },
  }"""),

    # ── S2 : Variante authorId (Blog, CMS) ───────────────────────────────────
    _std("20-dal-service", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/services/post.service.ts (modèle avec authorId)
RAISON: Certains modèles (Post, Article) utilisent authorId au lieu de userId. Le service doit utiliser le nom de champ exact du schéma Prisma — sinon TS2339 sur r.userId inexistant.
DETECTION_REGEX: r\\.userId.*authorId|where.*userId.*authorId
ALTERNATIVE: Utiliser le champ réel du modèle (authorId) dans tous les where et ownership checks
EXEMPLE_INVALIDE:
  findMany: (userId: string) => prisma.post.findMany({ where: { userId } })
  // Erreur : Post n'a pas de champ userId, il a authorId
EXEMPLE_VALIDE:
  export const postService = {
    findMany: (authorId: string) =>
      prisma.post.findMany({ where: { authorId }, orderBy: { createdAt: 'desc' } }),

    findUnique: async (id: string, userId: string) => {
      const r = await prisma.post.findUnique({ where: { id } })
      if (!r || r.authorId !== userId) return null
      return r
    },

    create: (data: { title: string; content: string; slug: string }, authorId: string) =>
      prisma.post.create({ data: { ...data, authorId } }),

    update: async (id: string, data: Partial<{ title: string; content: string }>, userId: string) => {
      const r = await prisma.post.findUnique({ where: { id } })
      if (!r || r.authorId !== userId) throw new Error('Forbidden')
      return prisma.post.update({ where: { id }, data })
    },

    delete: async (id: string, userId: string) => {
      const r = await prisma.post.findUnique({ where: { id } })
      if (!r || r.authorId !== userId) throw new Error('Forbidden')
      await prisma.post.delete({ where: { id } })
    },
  }"""),

    # ── S3 : Modèle enfant sans userId direct (Card → Board) ─────────────────
    _std("20-dal-service", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/services/card.service.ts (modèle enfant sans userId direct)
RAISON: Certains modèles (Card, Item, Comment) n'ont pas de userId — leur ownership est indirect via le modèle parent (Board, Project). Le service doit opérer par l'id du parent, pas par userId. L'ownership est vérifié au niveau de la route API en chargeant le parent.
DETECTION_REGEX: cardService.*userId|prisma\\.card\\.findMany.*userId
ALTERNATIVE: Utiliser boardId (ou l'id du parent) comme filtre — ne pas injecter userId dans findMany
EXEMPLE_INVALIDE:
  findMany: (userId: string) => prisma.card.findMany({ where: { userId } })
  // Erreur : Card n'a pas de champ userId → TS2353
EXEMPLE_VALIDE:
  export const cardService = {
    findManyByBoard: (boardId: string) =>
      prisma.card.findMany({ where: { boardId }, orderBy: { createdAt: 'asc' } }),

    create: (data: { title: string; column: string }, boardId: string) =>
      prisma.card.create({ data: { ...data, boardId } }),

    update: async (id: string, data: Partial<{ title: string; column: string }>) =>
      prisma.card.update({ where: { id }, data }),

    delete: async (id: string) =>
      prisma.card.delete({ where: { id } }),
  }
  // Note : dans la route API, vérifier que Board appartient à userId AVANT d'appeler cardService"""),

    # ── S4 : Import pattern dans les pages ───────────────────────────────────
    _std("20-dal-service", "services", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — import du service dans une page Server Component
RAISON: Les pages doivent importer l'objet service et appeler ses méthodes — jamais importer prisma directement depuis une page, et jamais importer des fonctions nommées inexistantes.
DETECTION_REGEX: import\\s+\\{\\s*get[A-Z][a-zA-Z]+\\s*\\}\\s+from\\s+'@/lib/services
ALTERNATIVE: Importer l'objet service et appeler la méthode appropriée
EXEMPLE_INVALIDE:
  import { getExpenses, getExpenseById } from '@/lib/services/expense.service'
  // Erreur TS2305 : ces exports n'existent pas
EXEMPLE_VALIDE:
  import { expenseService } from '@/lib/services/expense.service'

  export default async function ExpensesPage() {
    const { userId } = await auth()
    if (!userId) redirect('/sign-in')
    const expenses = await expenseService.findMany(userId)
    return (
      <main className="container mx-auto p-6">
        {expenses.length === 0 ? (
          <p>Aucune dépense.</p>
        ) : (
          <ul>{expenses.map(e => <li key={e.id}>{e.description} — {e.amount}€</li>)}</ul>
        )}
      </main>
    )
  }"""),

    # ── S5 : lib/types.ts — structure attendue ────────────────────────────────
    _std("20-dal-service", "types", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript — lib/types.ts
RAISON: lib/types.ts centralise les types partagés entre pages, services et routes API. Le LLM doit le générer en premier pour pouvoir l'importer dans les services et pages. Sans ce fichier, les imports depuis '@/lib/types' échouent avec TS2307.
DETECTION_REGEX: import.*from\\s+'@/lib/types'
ALTERNATIVE: Générer lib/types.ts en tout premier, avant les services et les pages
EXEMPLE_VALIDE:
  // lib/types.ts
  export type { Expense, Client, Invoice } from '@prisma/client'

  export type CreateExpenseInput = {
    amount: number
    category: string
    description: string
    date: string
  }
  export type UpdateExpenseInput = Partial<CreateExpenseInput>

  export type ApiResponse<T> = { data: T } | { error: string }
  export type PaginatedResponse<T> = { data: T[]; total: number }

  // Importer dans les services :
  // import type { CreateExpenseInput, UpdateExpenseInput } from '@/lib/types'"""),
]


# =============================================================================
# RUNNER
# =============================================================================

def run(dry_run: bool = False) -> None:
    client = QdrantClient(url=QDRANT_URL)
    standards = ZONE_20_DAL_SERVICE

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}ZONE_20 — {len(standards)} standards à injecter\n")

    points: list[PointStruct] = []
    for std in standards:
        text = std["text"]
        uid  = _uuid(text)
        if dry_run:
            print(f"  [{uid[:8]}] {text[:80].replace(chr(10), ' ')}...")
            continue
        vec = EMBEDDINGS.embed_query(text)
        points.append(PointStruct(id=uid, vector=vec, payload=std["metadata"] | {"text": text}))

    if dry_run:
        print(f"\n{len(standards)} points seraient injectés (dry-run — rien écrit).")
        return

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"✓ {len(points)} standards ZONE_20 injectés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
