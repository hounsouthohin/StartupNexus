import { defineConfig } from '@playwright/test';

// Tests d'écran par rôle (e2e/roles.spec.ts), joués sur l'app démarrée (BASE_URL).
export default defineConfig({
    testDir: 'e2e',
    workers: 1,
    timeout: 60_000,
    reporter: 'list',
    use: { baseURL: process.env.BASE_URL ?? 'http://localhost:3300', locale: 'fr-FR' },
});
