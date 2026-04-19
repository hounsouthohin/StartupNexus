"""
scripts/migrate_zones_17_18.py

Injecte deux nouvelles zones dans Qdrant factory_standards.
N'efface PAS les zones existantes (ZONE_1-16 restent intactes).

ZONE_17 — Patterns de code stack préventifs
  Exemples de code migrés depuis l'ancien rules_dev.md (190 lignes → 35 lignes).
  Récupérés par RAG avant la génération quand le LLM cherche "comment faire X".
  agent_context: dev

ZONE_18 — Standards correctifs par code d'erreur TypeScript
  Un standard par entrée du catalogue tsc_error_catalog.py.
  Récupérés via rag_query lors de la correction post-tsc ou post-build.
  agent_context: dev (correction phase)

COMMANDE :
  cd factory-sprint0
  python scripts/migrate_zones_17_18.py
  python scripts/migrate_zones_17_18.py --dry-run   # liste les IDs sans injecter

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

# ── Résolution du sys.path ────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.embedding_provider import get_embeddings, resolve_embedding_model
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

load_dotenv(dotenv_path=ROOT / ".env")

QDRANT_URL        = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME   = os.getenv("QDRANT_COLLECTION_NAME", "factory_standards")
EMBEDDING_MODEL   = resolve_embedding_model(os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"))
EMBEDDINGS        = get_embeddings(EMBEDDING_MODEL)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────

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
            "source": "migration-plan6",
            "agent_context": "dev",
        },
    }


# =============================================================================
# ZONE 17 — PATTERNS DE CODE STACK PRÉVENTIFS
# Migrés depuis rules_dev.md (exemples de code supprimés lors de la chirurgie)
# =============================================================================

ZONE_17_STACK_PATTERNS = [

    _std("17-stack-patterns", "nextjs", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: force-dynamic — ordre des déclarations dans un fichier Prisma
RAISON: export const dynamic doit être la première ligne avant les imports. TypeScript traite les exports de module avant les imports dans certains bundlers — un dynamic placé après les imports peut être ignoré en mode statique.
DETECTION_REGEX: ^import\\s+(?!.*force-dynamic)
ALTERNATIVE: Placer export const dynamic = 'force-dynamic' avant tout import
EXEMPLE_INVALIDE:
  import { NextResponse } from 'next/server';
  import prisma from '@/lib/prisma';
  export const dynamic = 'force-dynamic'; // ❌ trop tard
EXEMPLE_VALIDE:
  export const dynamic = 'force-dynamic'; // ✅ première ligne absolue
  import { NextResponse } from 'next/server';
  import { auth } from '@clerk/nextjs/server';
  import prisma from '@/lib/prisma';
ERREUR_ATTENDUE: PrismaClientInitializationError — ou build statique sans erreur mais crash runtime
STATUS: active
VERSION: 1.0"""),

    _std("17-stack-patterns", "prisma", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma singleton — import depuis @/lib/prisma uniquement
RAISON: Instancier PrismaClient directement crée N connexions pool en dev (HMR) et en prod. Le singleton lib/prisma.ts garantit une seule instance partagée via globalThis.
DETECTION_REGEX: new PrismaClient\\(\\)
ALTERNATIVE: import prisma from '@/lib/prisma'
EXEMPLE_INVALIDE:
  import { PrismaClient } from '@prisma/client';
  const prisma = new PrismaClient(); // ❌ nouvelle instance à chaque import
EXEMPLE_VALIDE:
  import prisma from '@/lib/prisma'; // ✅ singleton partagé
ERREUR_ATTENDUE: Too many connections — ou — PrismaClientKnownRequestError: connection pool exhausted
STATUS: active
VERSION: 1.0"""),

    _std("17-stack-patterns", "auth", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Clerk v6 — auth() guard pattern complet dans route handlers et pages server
RAISON: auth() retourne { userId: string | null }. Prisma attend String (non-nullable). TypeScript refuse de compiler where: { authorId: userId } si le guard est absent. Le guard sert à la fois au narrowing TypeScript ET à la sécurité runtime.
DETECTION_REGEX: await auth\\(\\)(?![\\s\\S]{0,200}if.*!userId)
ALTERNATIVE: Guard immédiat après auth()
EXEMPLE_INVALIDE:
  const { userId } = await auth();
  const items = await prisma.item.findMany({ where: { authorId: userId } }); // ❌ userId peut être null
EXEMPLE_VALIDE:
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  // ✅ userId est maintenant string (non-nullable) — TypeScript et Prisma acceptent
  const items = await prisma.item.findMany({ where: { authorId: userId } });
ERREUR_ATTENDUE: TS2345 — Argument of type 'string | null' is not assignable to parameter of type 'string'
STATUS: active
VERSION: 1.0"""),

    _std("17-stack-patterns", "auth", """ACTION: INTERDIT
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Clerk — authorId dans le body de la requête
RAISON: Accepter authorId depuis le body permet à un client malicieux d'associer une ressource à n'importe quel userId. L'authorId DOIT toujours venir de auth() côté serveur.
DETECTION_REGEX: body\\.authorId|req\\.json\\(\\)[\\s\\S]*authorId|authorId.*body
ALTERNATIVE: const { userId } = await auth(); puis data: { ...body, authorId: userId }
EXEMPLE_INVALIDE:
  const { title, authorId } = await req.json(); // ❌ authorId du client
  await prisma.post.create({ data: { title, authorId } });
EXEMPLE_VALIDE:
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const { title } = await req.json(); // ✅ pas d'authorId dans le body
  await prisma.post.create({ data: { title, authorId: userId } }); // ✅ userId de Clerk
ERREUR_ATTENDUE: Faille de sécurité — IDOR / privilege escalation
STATUS: active
VERSION: 1.0"""),

    _std("17-stack-patterns", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript strict — annotation explicite sur tableaux Prisma
RAISON: TypeScript infère never[] pour un tableau déclaré vide puis assigné dans un try/catch. La propriété 'id' n'existe pas sur type 'never' → TS2339 à la compilation. Pattern fetchAll avec .catch() résout le problème en une seule ligne.
DETECTION_REGEX: let \\w+ = \\[\\];[\\s\\S]{0,200}await prisma
ALTERNATIVE: const items: Model[] = await prisma.model.findMany().catch(() => [])
EXEMPLE_INVALIDE:
  let tasks = [];
  try {
    tasks = await prisma.task.findMany({ where: { userId } });
  } catch {
    tasks = [];
  }
  // ❌ TypeScript infère tasks: never[] — tasks[0].title → TS2339
EXEMPLE_VALIDE:
  const tasks: Task[] = await prisma.task.findMany({
    where: { userId },
  }).catch(() => []); // ✅ type explicite, gestion erreur en ligne
ERREUR_ATTENDUE: TS2339 — Property 'id' does not exist on type 'never'
STATUS: active
VERSION: 1.0"""),

    _std("17-stack-patterns", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript strict — types explicites sur callbacks React et destructurings
RAISON: TypeScript strict refuse les paramètres implicitement any (TS7006/TS7031). Les événements React et les destructurings de props doivent avoir des types explicites.
DETECTION_REGEX: onChange=\\{\\(e\\)\\s*=>|onSubmit=\\{\\(e\\)\\s*=>|function \\w+\\(\\{ \\w+ \\}\\)
ALTERNATIVE: Types explicites sur chaque paramètre de callback et destructuring
EXEMPLE_INVALIDE:
  onChange={(e) => setValue(e.target.value)}       // ❌ TS7006
  onSubmit={(e) => { e.preventDefault(); }}        // ❌ TS7006
  function Component({ id }) { ... }               // ❌ TS7031
EXEMPLE_VALIDE:
  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value)}   // ✅
  onSubmit={(e: React.FormEvent<HTMLFormElement>) => { e.preventDefault(); }}       // ✅
  function Component({ id }: { id: string }) { ... }                               // ✅
ERREUR_ATTENDUE: TS7006 — Parameter 'e' implicitly has an 'any' type
STATUS: active
VERSION: 1.0"""),

    _std("17-stack-patterns", "nextjs", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — imports obligatoires en tête de route handler
RAISON: L'absence d'un des trois imports dans un route handler provoque TS2552 (NextResponse non trouvé) ou TS2305 (auth non trouvé) à la compilation.
DETECTION_REGEX: export (async )?function (GET|POST|PUT|PATCH|DELETE)(?![\\s\\S]{0,300}import.*NextResponse)
ALTERNATIVE: Toujours présenter les trois imports en tête de fichier
EXEMPLE_INVALIDE:
  export const dynamic = 'force-dynamic';
  // ❌ import { NextResponse } manquant
  import { auth } from '@clerk/nextjs/server';
  import prisma from '@/lib/prisma';
  export async function GET() { return NextResponse.json({}) } // TS2552
EXEMPLE_VALIDE:
  export const dynamic = 'force-dynamic';
  import { NextResponse } from 'next/server';      // ✅
  import { auth } from '@clerk/nextjs/server';     // ✅
  import prisma from '@/lib/prisma';               // ✅
  export async function GET() { ... }
ERREUR_ATTENDUE: TS2552 — Cannot find name 'NextResponse'. Did you mean 'Response'?
STATUS: active
VERSION: 1.0"""),

    _std("17-stack-patterns", "auth", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Zod + Prisma — validation body avec authorId depuis auth() uniquement
RAISON: Deux erreurs fréquentes combinées : (1) passer result.data directement à Prisma expose des champs inattendus et ignore authorId ; (2) accepter authorId depuis le body = faille IDOR. Le pattern correct dissocie les champs validés du body et injecte authorId depuis auth().
DETECTION_REGEX: prisma\.\w+\.create\(\s*\{\s*data:\s*result\.data\s*\}
ALTERNATIVE: { data: { ...result.data, authorId: userId } } — authorId vient de auth(), jamais du body
EXEMPLE_INVALIDE:
  const result = CreateTaskSchema.safeParse(body);
  if (!result.success) return NextResponse.json({ error: result.error }, { status: 400 });
  await prisma.task.create({ data: result.data }); // ❌ authorId absent ou potentiellement dans body
EXEMPLE_VALIDE:
  const CreateTaskSchema = z.object({ title: z.string().min(1).max(255) });
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json();
  const result = CreateTaskSchema.safeParse(body);
  if (!result.success) return NextResponse.json({ error: result.error }, { status: 400 });
  await prisma.task.create({
    data: { ...result.data, authorId: userId }, // ✅ authorId de auth(), pas du body
  });
  return NextResponse.json(result.data, { status: 201 });
ERREUR_ATTENDUE: Faille IDOR si authorId du body / PrismaClientValidationError si authorId absent
STATUS: active
VERSION: 1.0"""),

    _std("17-stack-patterns", "nextjs", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Next.js App Router — use client sur composants avec hooks React
RAISON: Les pages app/**page.tsx sont Server Components par défaut. useState/useEffect ne peuvent s'exécuter que côté client. Sans "use client", Next.js lève une erreur runtime "hooks can only be called inside a function component".
DETECTION_REGEX: (useState|useEffect|useRef|useCallback)(?![\\s\\S]{0,50}"use client")
ALTERNATIVE: Ajouter "use client" en première ligne absolue du fichier
EXEMPLE_INVALIDE:
  import { useState } from 'react'; // ❌ Server Component par défaut
  export default function Form() {
    const [value, setValue] = useState('');
    return <input value={value} onChange={e => setValue(e.target.value)} />;
  }
EXEMPLE_VALIDE:
  "use client"; // ✅ première ligne
  import { useState } from 'react';
  export default function Form() {
    const [value, setValue] = useState('');
    return <input value={value} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value)} />;
  }
ERREUR_ATTENDUE: Error — useState can only be called inside a Client Component. Add the "use client" directive.
STATUS: active
VERSION: 1.0"""),

    _std("17-stack-patterns", "prisma", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: Prisma — accès aux propriétés déclarées dans schema.prisma uniquement
RAISON: Accéder à un champ absent du schema Prisma provoque TS2339 à la compilation. TypeScript génère les types depuis le schema — tout champ absent est un type error.
DETECTION_REGEX: N/A (détection par tsc)
ALTERNATIVE: Lire prisma/schema.prisma avant d'écrire des accès de champs — n'utiliser que les champs déclarés
EXEMPLE_INVALIDE:
  const task = await prisma.task.findUnique({ where: { id } });
  return task.deadline; // ❌ si 'deadline' absent du schema Task → TS2339
EXEMPLE_VALIDE:
  // schema.prisma : Task { id, title, done, dueDate, userId, createdAt }
  const task = await prisma.task.findUnique({ where: { id } });
  if (!task) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json({ id: task.id, title: task.title, dueDate: task.dueDate }); // ✅ champs déclarés
ERREUR_ATTENDUE: TS2339 — Property 'deadline' does not exist on type 'Task'
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ZONE 18 — STANDARDS CORRECTIFS PAR CODE D'ERREUR TYPESCRIPT
# Récupérés via rag_query depuis le catalogue tsc_error_catalog.py
# =============================================================================

ZONE_18_TSC_CORRECTIVE = [

    _std("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2307 — fichier local manquant (module cannot be found)
CODE_ERREUR: TS2307
RAISON: TS2307 sur un chemin local (@/, ./, ../) signifie que le fichier importé n'existe pas sur le disque — pas un problème de npm. Modifier l'import serait une erreur : le chemin est correct, c'est le fichier cible qui manque.
DETECTION_REGEX: error TS2307: Cannot find module '@/|\\./|\\.\\./'
DIAGNOSTIC: Identifier le chemin du module → convertir en chemin fichier (@/components/X → components/X.tsx) → créer le fichier avec write_file
EXEMPLE_INVALIDE:
  // app/page.tsx importe '@/components/TaskList' mais TaskList.tsx n'existe pas
  // ❌ Mauvaise réaction : modifier l'import en '@/components/task-list'
  // ❌ Mauvaise réaction : npm install ...
EXEMPLE_VALIDE:
  // ✅ Bonne réaction : créer components/TaskList.tsx
  write_file('components/TaskList.tsx', `
  "use client";
  import { Task } from '@/lib/types';
  interface Props { tasks: Task[] }
  export default function TaskList({ tasks }: Props) {
    return <ul>{tasks.map(t => <li key={t.id}>{t.title}</li>)}</ul>;
  }
  `)
RÈGLE_EXTENSION: .tsx si composant React (nom en majuscule, dans components/ ou app/) | .ts sinon
ERREUR_ATTENDUE: TS2307 Cannot find module '@/components/TaskList' or its corresponding type declarations.
STATUS: active
VERSION: 1.0"""),

    _std("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2339 never — annotation de type sur tableau Prisma
CODE_ERREUR: TS2339
RAISON: TypeScript infère never[] pour un tableau déclaré vide (let arr = []) puis assigné dans un try/catch. Toute propriété accédée sur never[] provoque TS2339. La solution est d'annoter explicitement le type du tableau au point de déclaration.
DETECTION_REGEX: error TS2339.*type 'never'
DIAGNOSTIC: Trouver la déclaration du tableau → ajouter annotation de type Model[] → utiliser pattern .catch(() => [])
EXEMPLE_INVALIDE:
  let tasks = []; // ❌ TypeScript infère never[]
  try {
    tasks = await prisma.task.findMany({ where: { userId } });
  } catch {
    tasks = [];
  }
  return tasks[0].id; // ❌ TS2339 : Property 'id' does not exist on type 'never'
EXEMPLE_VALIDE:
  // ✅ Option 1 : annotation explicite + catch inline
  const tasks: Task[] = await prisma.task.findMany({ where: { userId } }).catch(() => []);

  // ✅ Option 2 : annotation + try/catch
  let tasks: Task[] = [];
  try {
    tasks = await prisma.task.findMany({ where: { userId } });
  } catch {
    tasks = [];
  }
ERREUR_ATTENDUE: TS2339 — Property 'id' does not exist on type 'never'
STATUS: active
VERSION: 1.0"""),

    _std("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2304 — nom introuvable dans lib/types.ts
CODE_ERREUR: TS2304
RAISON: TS2304 "Cannot find name X" signifie que le type/interface/classe X n'est pas importé ou exporté dans le scope courant. Dans la factory, cela vise souvent des types générés dans lib/types.ts qui ont un nom différent du nom attendu.
DETECTION_REGEX: error TS2304: Cannot find name '\\w+'
DIAGNOSTIC: Lire lib/types.ts → identifier les exports réels → corriger l'utilisation ou l'import
ÉTAPES:
  1. read_file('lib/types.ts') — liste les exports réels
  2. Comparer avec le nom utilisé — souvent typo (CreatePostInput au lieu de CreateTaskInput)
  3. Corriger l'import ou le nom dans le fichier fautif
EXEMPLE_INVALIDE:
  import { CreatePostInput } from '@/lib/types'; // ❌ si lib/types.ts exporte CreateTaskInput
  const body: CreatePostInput = await req.json(); // TS2304
EXEMPLE_VALIDE:
  import { CreateTaskInput } from '@/lib/types'; // ✅ nom exact depuis lib/types.ts
  const body: CreateTaskInput = await req.json();
ERREUR_ATTENDUE: TS2304 — Cannot find name 'CreatePostInput'
STATUS: active
VERSION: 1.0"""),

    _std("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS7006/TS7031 — type explicite sur paramètre de callback React
CODE_ERREUR: TS7006
RAISON: TypeScript strict (noImplicitAny: true) refuse les paramètres de fonction sans type déclaré. Dans les composants React, les callbacks d'événements (onChange, onSubmit) et les destructurings de props doivent avoir des types explicites.
DETECTION_REGEX: error TS7006.*implicitly has an 'any' type|error TS7031.*implicitly has an 'any' type
DIAGNOSTIC: Identifier le paramètre non typé → ajouter le type React ou un type inline
TYPES_REACT_COURANTS:
  onChange input     → e: React.ChangeEvent<HTMLInputElement>
  onChange textarea  → e: React.ChangeEvent<HTMLTextAreaElement>
  onChange select    → e: React.ChangeEvent<HTMLSelectElement>
  onSubmit form      → e: React.FormEvent<HTMLFormElement>
  onClick button     → e: React.MouseEvent<HTMLButtonElement>
  destructuring prop → { id }: { id: string }
EXEMPLE_INVALIDE:
  onChange={(e) => setValue(e.target.value)}  // ❌ TS7006
  function Card({ id }) { ... }              // ❌ TS7031
EXEMPLE_VALIDE:
  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value)}  // ✅
  function Card({ id }: { id: string }) { ... }                                   // ✅
ERREUR_ATTENDUE: TS7006 — Parameter 'e' implicitly has an 'any' type
STATUS: active
VERSION: 1.0"""),

    _std("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2531 — null check avant accès sur résultat Prisma findUnique
CODE_ERREUR: TS2531
RAISON: prisma.model.findUnique() retourne Model | null. TypeScript refuse d'accéder à une propriété d'un objet potentiellement null sans guard préalable. Ce guard est aussi une bonne pratique API REST (404 si ressource introuvable).
DETECTION_REGEX: error TS2531: Object is possibly 'null'
DIAGNOSTIC: Ajouter un guard null après findUnique → retourner 404 si null
EXEMPLE_INVALIDE:
  const task = await prisma.task.findUnique({ where: { id } });
  return NextResponse.json({ id: task.id, title: task.title }); // ❌ TS2531 : task peut être null
EXEMPLE_VALIDE:
  const task = await prisma.task.findUnique({ where: { id } });
  if (!task) return NextResponse.json({ error: 'Not found' }, { status: 404 }); // ✅ guard null
  return NextResponse.json({ id: task.id, title: task.title }); // ✅ task est Task (non-null)
ERREUR_ATTENDUE: TS2531 — Object is possibly 'null'
STATUS: active
VERSION: 1.0"""),

    _std("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2345 — type 'string | null' non assignable à 'string' (auth guard)
CODE_ERREUR: TS2345
RAISON: auth() retourne { userId: string | null }. Prisma n'accepte pas string | null dans where: { authorId: userId }. Le narrowing TypeScript s'obtient uniquement avec un guard if (!userId) return 401 — après ce guard, userId est string.
DETECTION_REGEX: error TS2345.*'string \\| null'.*'string'
DIAGNOSTIC: Vérifier que le guard if (!userId) précède l'accès Prisma — si absent, l'ajouter
EXEMPLE_INVALIDE:
  const { userId } = await auth();
  const items = await prisma.item.findMany({
    where: { authorId: userId }, // ❌ TS2345 : string | null n'est pas string
  });
EXEMPLE_VALIDE:
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 }); // ✅ narrowing
  const items = await prisma.item.findMany({
    where: { authorId: userId }, // ✅ userId est string après le guard
  });
ERREUR_ATTENDUE: TS2345 — Argument of type 'string | null' is not assignable to parameter of type 'string'
STATUS: active
VERSION: 1.0"""),

    _std("18-tsc-corrective", "typescript", """ACTION: OBLIGATOIRE
STACK: nextjs-clerk-prisma
TECHNOLOGIE: TypeScript TS2339 — propriété absente du schema Prisma (champ inexistant)
CODE_ERREUR: TS2339
RAISON: Accéder à un champ non déclaré dans prisma/schema.prisma provoque TS2339. TypeScript génère les types Prisma depuis le schema — tout champ absent est une erreur de type. Ce n'est PAS une erreur never[] (cf. standard séparé) mais une vraie propriété manquante.
DETECTION_REGEX: error TS2339: Property '\\w+' does not exist on type '(?!never)\\w+'
DIAGNOSTIC: Lire prisma/schema.prisma → vérifier que le champ existe → corriger le nom ou ne pas y accéder
EXEMPLE_INVALIDE:
  // schema.prisma : Task { id, title, done, userId, createdAt }
  const task = await prisma.task.findUnique({ where: { id } });
  return task.deadline; // ❌ TS2339 : 'deadline' absent du schema
EXEMPLE_VALIDE:
  // schema.prisma : Task { id, title, done, dueDate, userId, createdAt }
  const task = await prisma.task.findUnique({ where: { id } });
  if (!task) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json({ id: task.id, title: task.title, dueDate: task.dueDate }); // ✅ champs déclarés
ERREUR_ATTENDUE: TS2339 — Property 'deadline' does not exist on type 'Task'
STATUS: active
VERSION: 1.0"""),
]


# =============================================================================
# ASSEMBLAGE
# =============================================================================

ALL_NEW_STANDARDS = [
    *[(i, s) for i, s in enumerate(ZONE_17_STACK_PATTERNS)],
    *[(i + len(ZONE_17_STACK_PATTERNS), s) for i, s in enumerate(ZONE_18_TSC_CORRECTIVE)],
]


# =============================================================================
# INJECTION QDRANT
# =============================================================================

def inject(dry_run: bool = False) -> None:
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Injection ZONE_17 ({len(ZONE_17_STACK_PATTERNS)} standards) + ZONE_18 ({len(ZONE_18_TSC_CORRECTIVE)} standards)")
    print(f"Collection : {COLLECTION_NAME}  |  Qdrant : {QDRANT_URL}\n")

    if dry_run:
        for _, std in ALL_NEW_STANDARDS:
            uid = _uuid(std["text"])
            zone = std["metadata"]["zone"]
            preview = std["text"].splitlines()[0][:80]
            print(f"  [{zone}] {uid}  {preview}")
        print(f"\n{len(ALL_NEW_STANDARDS)} standards listés (dry-run, rien injecté).")
        return

    client = QdrantClient(url=QDRANT_URL, timeout=30)

    texts = [s["text"] for _, s in ALL_NEW_STANDARDS]
    print(f"Génération embeddings ({len(texts)} textes)…")
    vectors = EMBEDDINGS.embed_documents(texts)
    print(f"Embeddings OK — dim={len(vectors[0])}")

    points = []
    for (_, std), vec in zip(ALL_NEW_STANDARDS, vectors):
        uid = _uuid(std["text"])
        points.append(PointStruct(
            id=uid,
            vector=vec,
            payload={
                "text": std["text"],
                **std["metadata"],
            },
        ))

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"\n✅ {len(points)} standards injectés dans '{COLLECTION_NAME}'.")
    print("   ZONE_17 : patterns de code préventifs (9 standards)")
    print("   ZONE_18 : correctifs tsc par code d'erreur (7 standards)")
    print("\nRien n'a été supprimé — ZONE_1-16 intactes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Injecte ZONE_17 + ZONE_18 dans Qdrant.")
    parser.add_argument("--dry-run", action="store_true", help="Liste les standards sans injecter.")
    args = parser.parse_args()
    inject(dry_run=args.dry_run)
