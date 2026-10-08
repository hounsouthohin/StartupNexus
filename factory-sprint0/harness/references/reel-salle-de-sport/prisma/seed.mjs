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
  const subscriptionRows = []
  subscriptionRows.push(await prisma.subscription.create({ data: { memberId: OWNER, status: 'active', renewalDate: new Date(Date.now() + 0 * 86400000) } }))
  subscriptionRows.push(await prisma.subscription.create({ data: { memberId: OWNER2, status: 'active', renewalDate: new Date(Date.now() + 1 * 86400000) } }))

  const courseRows = []
  courseRows.push(await prisma.course.create({ data: { title: 'Title exemple 1', description: 'Contenu de démonstration pour Course n°1.', schedule: new Date(Date.now() + 0 * 86400000) } }))
  courseRows.push(await prisma.course.create({ data: { title: 'Title exemple 2', description: 'Contenu de démonstration pour Course n°2.', schedule: new Date(Date.now() + 1 * 86400000) } }))

  const paymentRows = []
  paymentRows.push(await prisma.payment.create({ data: { subscriptionId: OWNER, amount: 42.50, date: new Date(Date.now() + 0 * 86400000) } }))
  paymentRows.push(await prisma.payment.create({ data: { subscriptionId: OWNER2, amount: 85.00, date: new Date(Date.now() + 1 * 86400000) } }))

  const memberRows = []
  memberRows.push(await prisma.member.create({ data: { userId: OWNER, subscriptionId: subscriptionRows[0].id } }))
  memberRows.push(await prisma.member.create({ data: { userId: OWNER2, subscriptionId: subscriptionRows[1].id } }))

  const reservationRows = []
  reservationRows.push(await prisma.reservation.create({ data: { courseId: OWNER, memberId: memberRows[0].id } }))
  reservationRows.push(await prisma.reservation.create({ data: { courseId: OWNER2, memberId: memberRows[1].id } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
