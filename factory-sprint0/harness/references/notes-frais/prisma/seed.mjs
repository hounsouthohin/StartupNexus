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
  const expenseReportRows = []
  expenseReportRows.push(await prisma.expenseReport.create({ data: { userId: OWNER, title: 'Title exemple 1', amount: 42.50, expenseDate: new Date(Date.now() + 0 * 86400000), category: 'transport', description: 'Contenu de démonstration pour ExpenseReport n°1.', status: 'draft' } }))
  expenseReportRows.push(await prisma.expenseReport.create({ data: { userId: OWNER, title: 'Title exemple 2', amount: 85.00, expenseDate: new Date(Date.now() + 1 * 86400000), category: 'transport', description: 'Contenu de démonstration pour ExpenseReport n°2.', status: 'draft' } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
