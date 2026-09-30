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
  clientRows.push(await prisma.client.create({ data: { userId: OWNER, name: 'Name exemple 1', phone: 'Phone exemple 1' } }))
  clientRows.push(await prisma.client.create({ data: { userId: OWNER2, name: 'Name exemple 2', phone: 'Phone exemple 2' } }))

  const vehicleRows = []
  vehicleRows.push(await prisma.vehicle.create({ data: { userId: OWNER, brand: 'Brand exemple 1', model: 'Model exemple 1', licensePlate: 'LicensePlate exemple 1', clientId: clientRows[0].id } }))
  vehicleRows.push(await prisma.vehicle.create({ data: { userId: OWNER2, brand: 'Brand exemple 2', model: 'Model exemple 2', licensePlate: 'LicensePlate exemple 2', clientId: clientRows[1].id } }))

  const repairRows = []
  repairRows.push(await prisma.repair.create({ data: { userId: OWNER, description: 'Contenu de démonstration pour Repair n°1.', status: 'pending', vehicleId: vehicleRows[0].id } }))
  repairRows.push(await prisma.repair.create({ data: { userId: OWNER2, description: 'Contenu de démonstration pour Repair n°2.', status: 'pending', vehicleId: vehicleRows[1].id } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
