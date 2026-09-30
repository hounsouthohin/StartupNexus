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
  const spaceRows = []
  spaceRows.push(await prisma.space.create({ data: { name: 'Name exemple 1', description: 'Contenu de démonstration pour Space n°1.', type: 'private_office', capacity: 10, hourlyRate: 42.50, address: 'Address exemple 1' } }))
  spaceRows.push(await prisma.space.create({ data: { name: 'Name exemple 2', description: 'Contenu de démonstration pour Space n°2.', type: 'private_office', capacity: 20, hourlyRate: 85.00, address: 'Address exemple 2' } }))

  const memberRows = []
  memberRows.push(await prisma.member.create({ data: { userId: OWNER, name: 'Name exemple 1', email: 'demo1@example.com', company: 'Company exemple 1', phone: 'Phone exemple 1' } }))
  memberRows.push(await prisma.member.create({ data: { userId: OWNER2, name: 'Name exemple 2', email: 'demo2@example.com', company: 'Company exemple 2', phone: 'Phone exemple 2' } }))

  const reservationRows = []
  reservationRows.push(await prisma.reservation.create({ data: { userId: OWNER, date: new Date(Date.now() + 0 * 86400000), startTime: new Date(Date.now() + 0 * 86400000), endTime: new Date(Date.now() + 0 * 86400000), status: 'requested', spaceId: spaceRows[0].id, memberId: memberRows[0].id } }))
  reservationRows.push(await prisma.reservation.create({ data: { userId: OWNER2, date: new Date(Date.now() + 1 * 86400000), startTime: new Date(Date.now() + 1 * 86400000), endTime: new Date(Date.now() + 1 * 86400000), status: 'requested', spaceId: spaceRows[1].id, memberId: memberRows[1].id } }))

  const invoiceRows = []
  invoiceRows.push(await prisma.invoice.create({ data: { userId: OWNER, amount: 42.50, issueDate: new Date(Date.now() + 0 * 86400000), status: 'pending', reservationId: reservationRows[0].id } }))
  invoiceRows.push(await prisma.invoice.create({ data: { userId: OWNER2, amount: 85.00, issueDate: new Date(Date.now() + 1 * 86400000), status: 'pending', reservationId: reservationRows[1].id } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
