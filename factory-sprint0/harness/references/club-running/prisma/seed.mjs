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
  const runEventRows = []
  runEventRows.push(await prisma.runEvent.create({ data: { userId: OWNER, title: 'Title exemple 1', dateTime: new Date(Date.now() + 0 * 86400000), location: 'Location exemple 1', distance: 42.50, description: 'Contenu de démonstration pour RunEvent n°1.', status: 'ouverte' } }))
  runEventRows.push(await prisma.runEvent.create({ data: { userId: OWNER, title: 'Title exemple 2', dateTime: new Date(Date.now() + 1 * 86400000), location: 'Location exemple 2', distance: 85.00, description: 'Contenu de démonstration pour RunEvent n°2.', status: 'ouverte' } }))

  const participantRows = []
  participantRows.push(await prisma.participant.create({ data: { userId: OWNER, name: 'Name exemple 1', email: 'demo1@example.com', runEventId: runEventRows[0].id } }))
  participantRows.push(await prisma.participant.create({ data: { userId: OWNER, name: 'Name exemple 2', email: 'demo2@example.com', runEventId: runEventRows[1].id } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
