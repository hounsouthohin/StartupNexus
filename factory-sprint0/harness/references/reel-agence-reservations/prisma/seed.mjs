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
  const clientRows = []
  clientRows.push(await prisma.client.create({ data: { providerId: OWNER, name: 'Name exemple 1', email: 'demo1@example.com' } }))
  clientRows.push(await prisma.client.create({ data: { providerId: OWNER2, name: 'Name exemple 2', email: 'demo2@example.com' } }))

  const providerRows = []
  providerRows.push(await prisma.provider.create({ data: { name: 'Name exemple 1', email: 'demo1@example.com' } }))
  providerRows.push(await prisma.provider.create({ data: { name: 'Name exemple 2', email: 'demo2@example.com' } }))

  const managerRows = []
  managerRows.push(await prisma.manager.create({ data: { name: 'Name exemple 1', email: 'demo1@example.com' } }))
  managerRows.push(await prisma.manager.create({ data: { name: 'Name exemple 2', email: 'demo2@example.com' } }))

  const reservationRows = []
  reservationRows.push(await prisma.reservation.create({ data: { clientId: OWNER, date: new Date(Date.now() + 0 * 86400000), status: 'pending', providerId: providerRows[0].id, managerId: managerRows[0].id } }))
  reservationRows.push(await prisma.reservation.create({ data: { clientId: OWNER2, date: new Date(Date.now() + 1 * 86400000), status: 'pending', providerId: providerRows[1].id, managerId: managerRows[1].id } }))

  const alertRows = []
  alertRows.push(await prisma.alert.create({ data: { userId: OWNER, message: 'Contenu de démonstration pour Alert n°1.', reservationId: reservationRows[0].id } }))
  alertRows.push(await prisma.alert.create({ data: { userId: OWNER2, message: 'Contenu de démonstration pour Alert n°2.', reservationId: reservationRows[1].id } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
