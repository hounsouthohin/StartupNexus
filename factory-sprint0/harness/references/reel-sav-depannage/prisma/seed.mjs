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
  const clientRows = []
  clientRows.push(await prisma.client.create({ data: { userId: OWNER, name: 'Name exemple 1', email: 'demo1@example.com', address: 'Address exemple 1' } }))
  clientRows.push(await prisma.client.create({ data: { userId: OWNER, name: 'Name exemple 2', email: 'demo2@example.com', address: 'Address exemple 2' } }))

  const machineRows = []
  machineRows.push(await prisma.machine.create({ data: { userId: OWNER, model: 'Model exemple 1', serialNumber: 'SerialNumber exemple 1', socket: '478', clientId: clientRows[0].id } }))
  machineRows.push(await prisma.machine.create({ data: { userId: OWNER, model: 'Model exemple 2', serialNumber: 'SerialNumber exemple 2', socket: '478', clientId: clientRows[1].id } }))

  const interventionRows = []
  interventionRows.push(await prisma.intervention.create({ data: { userId: OWNER, date: new Date(Date.now() + 0 * 86400000), status: 'ouverte', machineId: machineRows[0].id } }))
  interventionRows.push(await prisma.intervention.create({ data: { userId: OWNER, date: new Date(Date.now() + 1 * 86400000), status: 'ouverte', machineId: machineRows[1].id } }))

  const actionRows = []
  actionRows.push(await prisma.action.create({ data: { userId: OWNER, description: 'Contenu de démonstration pour Action n°1.', status: 'a_faire', interventionId: interventionRows[0].id } }))
  actionRows.push(await prisma.action.create({ data: { userId: OWNER, description: 'Contenu de démonstration pour Action n°2.', status: 'a_faire', interventionId: interventionRows[1].id } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
