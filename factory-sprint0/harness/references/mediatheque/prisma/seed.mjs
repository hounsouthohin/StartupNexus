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
  const bookRows = []
  bookRows.push(await prisma.book.create({ data: { title: 'Title exemple 1', author: 'Author exemple 1', summary: 'Summary exemple 1', genre: 'roman', publicationYear: 10 } }))
  bookRows.push(await prisma.book.create({ data: { title: 'Title exemple 2', author: 'Author exemple 2', summary: 'Summary exemple 2', genre: 'roman', publicationYear: 20 } }))

  const memberRows = []
  memberRows.push(await prisma.member.create({ data: { userId: OWNER, name: 'Name exemple 1', email: 'demo1@example.com', phone: 'Phone exemple 1' } }))
  memberRows.push(await prisma.member.create({ data: { userId: OWNER2, name: 'Name exemple 2', email: 'demo2@example.com', phone: 'Phone exemple 2' } }))

  const borrowingRows = []
  borrowingRows.push(await prisma.borrowing.create({ data: { userId: OWNER, status: 'requested', bookId: bookRows[0].id } }))
  borrowingRows.push(await prisma.borrowing.create({ data: { userId: OWNER2, status: 'requested', bookId: bookRows[1].id } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
