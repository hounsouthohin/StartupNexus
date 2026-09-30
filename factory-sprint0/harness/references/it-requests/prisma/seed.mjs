// AUTO-GÉNÉRÉ PAR dev_seed_generator.py — données de démonstration (Preview local).
// JS pur (.mjs) → lancé par `node prisma/seed.mjs`, sans tsx ni build. Dev-only.
// Lancer : DATABASE_URL=... SEED_USER_ID=<votre-id-clerk> node prisma/seed.mjs
// Prisma 7 exige un driver adapter (comme lib/prisma.ts) — un new PrismaClient() nu échoue.
import { PrismaClient } from '@prisma/client'
import { PrismaPg } from '@prisma/adapter-pg'
import { Pool } from 'pg'

const pool = new Pool({ connectionString: process.env.DATABASE_URL })
const adapter = new PrismaPg(pool)
const prisma = new PrismaClient({ adapter })
const OWNER = process.env.SEED_USER_ID ?? 'user_demo'
const OWNER2 = process.env.SEED_USER_ID_2 ?? 'user_demo_2'

async function main() {
  const requestRows = []
  requestRows.push(await prisma.request.create({ data: { userId: OWNER, title: 'Title exemple 1', description: 'Contenu de démonstration pour Request n°1.', priority: 'low', status: 'new' } }))
  requestRows.push(await prisma.request.create({ data: { userId: OWNER2, title: 'Title exemple 2', description: 'Contenu de démonstration pour Request n°2.', priority: 'low', status: 'new' } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
