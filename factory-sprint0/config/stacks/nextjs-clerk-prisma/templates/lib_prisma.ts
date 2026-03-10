import * as PrismaPkg from '@prisma/client';

type PrismaClientCtor = new (...args: any[]) => any;

// Prisma 7 peut exposer PrismaClient différemment selon le generator/provider.
// On résout la classe au runtime pour éviter les erreurs TS "no exported member".
const PrismaClientCompat: PrismaClientCtor =
  (PrismaPkg as any).PrismaClient ||
  (PrismaPkg as any).default?.PrismaClient ||
  (PrismaPkg as any).default;

if (!PrismaClientCompat) {
  throw new Error(
    "PrismaClient introuvable dans @prisma/client. Vérifie prisma/schema.prisma (generator provider) puis relance prisma generate."
  );
}

const globalForPrisma = globalThis as unknown as { prisma?: any };
const datasourceUrl =
  process.env.DATABASE_URL ||
  'postgresql://user:password@localhost:5432/postgres';

const prisma =
  globalForPrisma.prisma ??
  new PrismaClientCompat({
    datasources: {
      db: { url: datasourceUrl },
    },
  });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

export default prisma;
