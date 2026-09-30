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
  const recipeRows = []
  recipeRows.push(await prisma.recipe.create({ data: { userId: OWNER, title: 'Title exemple 1', instructions: 'Instructions exemple 1', preparationTime: 10, difficulty: 'facile', published: true, slug: 'exemple-recipe-1' } }))
  recipeRows.push(await prisma.recipe.create({ data: { userId: OWNER, title: 'Title exemple 2', instructions: 'Instructions exemple 2', preparationTime: 20, difficulty: 'facile', published: false, slug: 'exemple-recipe-2' } }))

  const tagRows = []
  tagRows.push(await prisma.tag.create({ data: { userId: OWNER, name: 'Name exemple 1' } }))
  tagRows.push(await prisma.tag.create({ data: { userId: OWNER, name: 'Name exemple 2' } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
