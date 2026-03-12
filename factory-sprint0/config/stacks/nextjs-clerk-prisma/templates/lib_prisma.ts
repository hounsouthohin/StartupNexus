import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma?: any };

const datasourceUrl =
  process.env.DATABASE_URL ||
  'postgresql://user:password@localhost:5432/postgres';

const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({ datasourceUrl });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

export default prisma;
