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

async function main() {
  const categoryRows = []
  categoryRows.push(await prisma.category.create({ data: { userId: OWNER, name: 'Name exemple 1', description: 'Contenu de démonstration pour Category n°1.' } }))
  categoryRows.push(await prisma.category.create({ data: { userId: OWNER, name: 'Name exemple 2', description: 'Contenu de démonstration pour Category n°2.' } }))

  const subscriptionRows = []
  subscriptionRows.push(await prisma.subscription.create({ data: { userId: OWNER, name: 'Name exemple 1', monthlyPrice: 42.50, nextBillingDate: new Date(Date.now() + 0 * 86400000), status: 'active', categoryId: categoryRows[0].id } }))
  subscriptionRows.push(await prisma.subscription.create({ data: { userId: OWNER, name: 'Name exemple 2', monthlyPrice: 85.00, nextBillingDate: new Date(Date.now() + 1 * 86400000), status: 'active', categoryId: categoryRows[1].id } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
