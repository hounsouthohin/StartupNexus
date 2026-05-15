import { defineConfig } from 'prisma/config';
import { config } from 'dotenv';
config({ path: '.env.local' });

const databaseUrl =
  process.env.DATABASE_URL ||
  'postgresql://user:password@localhost:5432/postgres';

export default defineConfig({
  schema: 'prisma/schema.prisma',
  datasource: { url: databaseUrl },
});
