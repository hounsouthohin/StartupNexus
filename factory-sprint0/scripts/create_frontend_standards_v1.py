"""
scripts/create_frontend_standards_v1.py

Standards Frontend — Design UI Type A (CRUD SaaS) et Type D (Blog/CMS).
Injectés dans Qdrant collection factory_standards avec agent_context="frontend".

FORMAT : Option A (RULE:/WHY:/GOOD:/BAD:)
Zone : frontend-type-a, frontend-type-d

PROCÉDURE :
  python scripts/create_frontend_standards_v1.py
  (n'efface PAS les autres standards — upsert idempotent par UUID MD5)
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from agents.embedding_provider import get_embedding_provider, get_embeddings, resolve_embedding_model
except ModuleNotFoundError:
    from agents.embedding_provider import get_embedding_provider, get_embeddings, resolve_embedding_model

from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

load_dotenv(dotenv_path=".env")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
EMBEDDING_MODEL = resolve_embedding_model(os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"))
EMBEDDING_PROVIDER = get_embedding_provider()
EMBEDDINGS = get_embeddings(EMBEDDING_MODEL)


def text_to_uuid(text: str) -> str:
    hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
    return str(UUID(bytes=hash_bytes))


# =============================================================================
# ZONE FRONTEND-TYPE-A — CRUD SaaS avec sidebar navigation
# =============================================================================

FRONTEND_TYPE_A = [
    {
        "text": """\
RULE: DashboardShell — sidebar "use client" avec usePathname active link detection
WHY: Sans DashboardShell, les pages privées n'ont aucune navigation — l'app semble cassée. Le composant doit être "use client" pour que usePathname fonctionne. Sans isAuthPage guard, la sidebar s'affiche sur /sign-in et /sign-up.
GOOD:
"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { UserButton } from "@clerk/nextjs"
import { LayoutDashboard, Users, Settings } from "lucide-react"

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { href: "/dashboard/users", label: "Utilisateurs", icon: Users },
  { href: "/dashboard/settings", label: "Paramètres", icon: Settings },
]

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isAuthPage = pathname.startsWith("/sign-in") || pathname.startsWith("/sign-up")
  if (isAuthPage) return <>{children}</>
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <aside className="w-60 shrink-0 bg-white border-r border-gray-200 flex flex-col">
        <div className="h-14 flex items-center px-5 border-b">
          <span className="font-semibold text-gray-900">Mon App</span>
        </div>
        <nav className="flex-1 px-3 py-3 space-y-0.5">
          {NAV.map(({ href, label, icon: Icon, exact }) => {
            const active = exact ? pathname === href : pathname === href || pathname.startsWith(href + "/")
            return (
              <Link key={href} href={href}
                className={["flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium",
                  active ? "bg-blue-50 text-blue-700" : "text-gray-600 hover:bg-gray-100"].join(" ")}>
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            )
          })}
        </nav>
        <div className="p-3 border-t border-gray-200">
          <UserButton />
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}
BAD:
// Pas de "use client" → usePathname crash en Server Component
// Pas de isAuthPage guard → sidebar visible sur /sign-in
// Pas de UserButton → utilisateur ne peut pas se déconnecter
// Sidebar hardcodée sans les nav links du spec → navigation incomplète""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "frontend-type-a",
            "status": "deprecated",  # remplacé par templates/generators déterministes
            "version": "1.0",
            "category": "frontend",
            "source": "factory_standards_frontend_v1",
            "agent_context": "frontend",
        },
    },
    {
        "text": """\
RULE: List page — Table avec hover rows, boutons icon+texte, empty state avec CTA
WHY: Une page liste sans design ressemble à du HTML brut. Le Table du design system gère le hover et les colonnes. L'empty state avec CTA évite la confusion "l'app est cassée".
GOOD:
import { Table, Button, Empty, Badge } from "@/app/components/ui"
import { Plus, Pencil, Trash2 } from "lucide-react"
import Link from "next/link"

export default function ItemsPageClient({ items }: { items: Item[] }) {
  if (items.length === 0) {
    return (
      <div className="p-6">
        <Empty
          title="Aucun élément"
          description="Créez votre premier élément pour commencer."
          action={<Link href="/dashboard/items/new"><Button variant="primary"><Plus className="w-4 h-4 mr-2"/>Nouvel élément</Button></Link>}
        />
      </div>
    )
  }
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Éléments</h1>
        <Link href="/dashboard/items/new">
          <Button variant="primary"><Plus className="w-4 h-4 mr-2"/>Nouvel élément</Button>
        </Link>
      </div>
      <Table
        columns={[
          { key: "name", label: "Nom" },
          { key: "status", label: "Statut", render: (row) => <Badge variant={row.status === "active" ? "success" : "neutral"}>{row.status}</Badge> },
        ]}
        rows={items}
        actions={(row) => (
          <div className="flex gap-2">
            <Link href={`/dashboard/items/${row.id}/edit`}><Button variant="ghost" size="sm"><Pencil className="w-4 h-4"/></Button></Link>
            <form action={deleteItem.bind(null, row.id)}><Button variant="danger" size="sm"><Trash2 className="w-4 h-4"/></Button></form>
          </div>
        )}
      />
    </div>
  )
}
BAD:
// Liste de liens <a> sans style, pas de tableau, pas d'empty state
// Boutons sans icônes — interface non professionnelle""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "frontend-type-a",
            "status": "deprecated",  # remplacé par templates/generators déterministes
            "version": "1.0",
            "category": "frontend",
            "source": "factory_standards_frontend_v1",
            "agent_context": "frontend",
        },
    },
    {
        "text": """\
RULE: Form page — champs labelisés, zone erreur visible, bouton submit proéminent
WHY: Un formulaire sans labels ni feedback d'erreur est inutilisable. La zone erreur doit être visible AVANT le submit (pattern useActionState).
GOOD:
"use client"
import { useActionState } from "react"
import { Button } from "@/app/components/ui"
import { createItem } from "./actions"

export default function NewItemPageClient() {
  const [state, action, pending] = useActionState(createItem, null)
  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Nouvel élément</h1>
      <form action={action} className="space-y-5 bg-white rounded-xl border border-gray-200 p-6">
        {state?.error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{state.error}</div>
        )}
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-gray-700">Nom *</label>
          <input name="name" required
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={() => history.back()}>Annuler</Button>
          <Button type="submit" variant="primary" disabled={pending}>
            {pending ? "Création..." : "Créer"}
          </Button>
        </div>
      </form>
    </div>
  )
}
BAD:
// inputs sans labels — inaccessible
// pas de zone erreur → utilisateur ne sait pas ce qui a échoué
// bouton submit sans état pending → double-submit possible""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "frontend-type-a",
            "status": "deprecated",  # remplacé par templates/generators déterministes
            "version": "1.0",
            "category": "frontend",
            "source": "factory_standards_frontend_v1",
            "agent_context": "frontend",
        },
    },
    {
        "text": """\
RULE: Dashboard home page — StatCards avec données réelles, section actions rapides
WHY: Un dashboard vide ou avec de fausses données ne donne aucune valeur. Les StatCard affichent les comptes réels depuis le serveur. Les actions rapides évitent la navigation à l'aveugle.
GOOD:
import { StatCard, Card, Button } from "@/app/components/ui"
import { Plus, BarChart2, Users } from "lucide-react"
import Link from "next/link"

export default function DashboardPageClient({ stats }: { stats: { total: number; active: number } }) {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Tableau de bord</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard label="Total éléments" value={stats.total} trendDirection="flat" />
        <StatCard label="Actifs" value={stats.active} trendDirection="up" trend="+2 cette semaine" />
      </div>
      <Card title="Actions rapides" description="Commencez par créer ou consulter">
        <div className="flex gap-3 flex-wrap">
          <Link href="/dashboard/items/new"><Button variant="primary"><Plus className="w-4 h-4 mr-2"/>Nouvel élément</Button></Link>
          <Link href="/dashboard/items"><Button variant="secondary"><BarChart2 className="w-4 h-4 mr-2"/>Voir tout</Button></Link>
        </div>
      </Card>
    </div>
  )
}
BAD:
// Stats hardcodées (0, 42) au lieu de données réelles
// Dashboard = simple liste de liens sans métriques
// Aucune action rapide — utilisateur doit naviguer via la sidebar""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "frontend-type-a",
            "status": "deprecated",  # remplacé par templates/generators déterministes
            "version": "1.0",
            "category": "frontend",
            "source": "factory_standards_frontend_v1",
            "agent_context": "frontend",
        },
    },
]


# =============================================================================
# ZONE FRONTEND-TYPE-D — Blog/CMS avec dual layout (public + privé)
# =============================================================================

FRONTEND_TYPE_D = [
    {
        "text": """\
RULE: Dual layout Blog/CMS — topnav public + sidebar privée dans DashboardShell
WHY: Un blog a deux types de pages : pages publiques (article list, article detail) avec une topnav, et pages privées (dashboard, éditeur) avec une sidebar. DashboardShell doit détecter si la route est publique et switcher le layout.
GOOD:
export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isAuthPage = pathname.startsWith("/sign-in") || pathname.startsWith("/sign-up")
  const isPublicPage = !pathname.startsWith("/dashboard") && !isAuthPage
  if (isAuthPage) return <>{children}</>
  if (isPublicPage) {
    return (
      <div className="min-h-screen bg-white">
        <header className="border-b border-gray-200 sticky top-0 bg-white/95 backdrop-blur z-10">
          <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
            <Link href="/" className="font-bold text-gray-900">Mon Blog</Link>
            <nav className="flex gap-6 text-sm text-gray-600">
              <Link href="/articles" className="hover:text-gray-900">Articles</Link>
              <Link href="/sign-in"><Button variant="primary" size="sm">Connexion</Button></Link>
            </nav>
          </div>
        </header>
        <main>{children}</main>
      </div>
    )
  }
  // Layout privé avec sidebar
  return (
    <div className="flex h-screen">
      <aside>...</aside>
      <main>{children}</main>
    </div>
  )
}
BAD:
// Sidebar privée sur toutes les pages — les articles publics ont une sidebar bizarre
// Topnav sur toutes les pages — le dashboard auteur ressemble à un blog public""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "frontend-type-d",
            "status": "deprecated",  # remplacé par templates/generators déterministes
            "version": "1.0",
            "category": "frontend",
            "source": "factory_standards_frontend_v1",
            "agent_context": "frontend",
        },
    },
    {
        "text": """\
RULE: Article card design — cover image placeholder, badge catégorie, date formatée, lien cliquable
WHY: Les cards d'articles sans visuel ou sans date/catégorie semblent génériques. Un article card professionnel a un accent couleur, un badge, et un lien couvrant toute la carte.
GOOD:
import { Badge } from "@/app/components/ui"
import Link from "next/link"

function ArticleCard({ article }: { article: Article }) {
  return (
    <Link href={`/articles/${article.slug}`} className="group block rounded-xl border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="aspect-video bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <span className="text-4xl">{article.emoji || "📝"}</span>
      </div>
      <div className="p-4 space-y-2">
        <div className="flex items-center gap-2">
          <Badge variant="info">{article.category}</Badge>
          <span className="text-xs text-gray-400">{new Date(article.publishedAt).toLocaleDateString("fr-FR")}</span>
        </div>
        <h2 className="font-semibold text-gray-900 group-hover:text-blue-700 line-clamp-2">{article.title}</h2>
        <p className="text-sm text-gray-500 line-clamp-2">{article.excerpt}</p>
      </div>
    </Link>
  )
}

export default function ArticlesPageClient({ articles }: { articles: Article[] }) {
  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Articles</h1>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {articles.map(a => <ArticleCard key={a.id} article={a} />)}
      </div>
    </div>
  )
}
BAD:
// Liste de titres sans visuel — ressemble à du Markdown brut
// Cards sans hover state — pas d'affordance de clic""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "frontend-type-d",
            "status": "deprecated",  # remplacé par templates/generators déterministes
            "version": "1.0",
            "category": "frontend",
            "source": "factory_standards_frontend_v1",
            "agent_context": "frontend",
        },
    },
    {
        "text": """\
RULE: Status badge pour CMS — draft/published/archived avec couleurs distinctives
WHY: Dans un CMS, le statut d'un article est l'information la plus critique pour l'auteur. Les statuts doivent être visuellement distincts et immédiatement lisibles dans la liste.
GOOD:
import { Badge } from "@/app/components/ui"

const STATUS_CONFIG = {
  draft:     { variant: "warning" as const, label: "Brouillon" },
  published: { variant: "success" as const, label: "Publié" },
  archived:  { variant: "neutral" as const, label: "Archivé" },
}

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] ?? { variant: "neutral" as const, label: status }
  return <Badge variant={config.variant}>{config.label}</Badge>
}

// Dans la liste auteur (dashboard)
columns={[
  { key: "title", label: "Titre" },
  { key: "status", label: "Statut", render: (row) => <StatusBadge status={row.status} /> },
  { key: "publishedAt", label: "Date", render: (row) => row.publishedAt ? new Date(row.publishedAt).toLocaleDateString("fr-FR") : "—" },
]}
BAD:
// Statut affiché en texte brut sans couleur — draft, published, archived se ressemblent
// Pas de distinction visuelle → l'auteur publie accidentellement des brouillons""",
        "metadata": {
            "stack": "nextjs-clerk-prisma",
            "zone": "frontend-type-d",
            "status": "deprecated",  # remplacé par templates/generators déterministes
            "version": "1.0",
            "category": "frontend",
            "source": "factory_standards_frontend_v1",
            "agent_context": "frontend",
        },
    },
]


# =============================================================================
# Injection Qdrant
# =============================================================================

ALL_STANDARDS = [
    (i, std)
    for i, std in enumerate(FRONTEND_TYPE_A + FRONTEND_TYPE_D)
]


def inject_standards() -> None:
    client = QdrantClient(url=QDRANT_URL)

    # Verify collection exists
    try:
        client.get_collection(COLLECTION_NAME)
    except Exception:
        print(f"[ERROR] Collection '{COLLECTION_NAME}' introuvable — lancez reset_qdrant.py d'abord.")
        return

    points: list[PointStruct] = []
    total = len(ALL_STANDARDS)

    for idx, (_, std) in enumerate(ALL_STANDARDS, 1):
        text = std["text"]
        metadata = std["metadata"]
        uid = text_to_uuid(text)

        print(f"[{idx}/{total}] Embedding zone={metadata['zone']} ...", end=" ", flush=True)
        try:
            vector = EMBEDDINGS.embed_query(text)
        except Exception as e:
            print(f"ERREUR embedding: {e}")
            continue

        points.append(PointStruct(
            id=uid,
            vector=vector,
            payload={"text": text, "metadata": metadata},
        ))
        print(f"OK (uuid={uid[:8]}...)")

    if not points:
        print("[WARN] Aucun point à injecter.")
        return

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"\n[OK] {len(points)} standards frontend injectés dans '{COLLECTION_NAME}'")
    print(f"     Type A: {len(FRONTEND_TYPE_A)} standards")
    print(f"     Type D: {len(FRONTEND_TYPE_D)} standards")


if __name__ == "__main__":
    inject_standards()
