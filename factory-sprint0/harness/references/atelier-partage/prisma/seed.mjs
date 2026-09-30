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
  const workshopRows = []
  workshopRows.push(await prisma.workshop.create({ data: { title: 'Title exemple 1', description: 'Contenu de démonstration pour Workshop n°1.', duration: 10, price: 42.50 } }))
  workshopRows.push(await prisma.workshop.create({ data: { title: 'Title exemple 2', description: 'Contenu de démonstration pour Workshop n°2.', duration: 20, price: 85.00 } }))

  const domainRows = []
  domainRows.push(await prisma.domain.create({ data: { name: 'Name exemple 1' } }))
  domainRows.push(await prisma.domain.create({ data: { name: 'Name exemple 2' } }))

  const slotRows = []
  slotRows.push(await prisma.slot.create({ data: { workshopId: OWNER, startTime: new Date(Date.now() + 0 * 86400000), endTime: new Date(Date.now() + 0 * 86400000) } }))
  slotRows.push(await prisma.slot.create({ data: { workshopId: OWNER2, startTime: new Date(Date.now() + 1 * 86400000), endTime: new Date(Date.now() + 1 * 86400000) } }))

  const reservationRows = []
  reservationRows.push(await prisma.reservation.create({ data: { userId: OWNER, status: 'pending', slotId: slotRows[0].id } }))
  reservationRows.push(await prisma.reservation.create({ data: { userId: OWNER2, status: 'pending', slotId: slotRows[1].id } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
