import { defineConfig } from '@playwright/test';

// Tests par rôle, identiques pour les deux variantes (app démarrée : npx next start -p 3200).
export default defineConfig({
    testDir: 'e2e',
    workers: 1,
    timeout: 60_000,
    use: { baseURL: 'http://localhost:3200', locale: 'fr-FR', viewport: { width: 1100, height: 700 } },
});
