import { defineConfig } from 'prisma/config';
import { config } from 'dotenv';

// Charge .env.local pour les commandes CLI (prisma generate, prisma db push)
// DATABASE_URL et DIRECT_DATABASE_URL sont définis dans schema.prisma via env()
config({ path: '.env.local' });

export default defineConfig({
  schema: 'prisma/schema.prisma',
});
