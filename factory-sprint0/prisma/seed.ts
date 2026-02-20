import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  // Seed initial data if necessary
  const user = await prisma.user.create({
    data: {
      email: 'example@example.com',
      name: 'Example User',
    },
  });
  console.log({ user });
}

main()
  .catch((e) => console.error(e))
  .finally(async () => {
    await prisma.$disconnect();
  });