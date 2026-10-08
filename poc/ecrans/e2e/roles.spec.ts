// Les MÊMES tests par rôle pour la variante A (Refine) et la variante B (nos pièces).
import { expect, test, type BrowserContext } from '@playwright/test';
import { execSync } from 'node:child_process';

const BASE = 'http://localhost:3200';
const seConnecter = (context: BrowserContext, qui: string) =>
    context.addCookies([{ name: 'poc_user', value: qui, url: BASE }]);

for (const v of ['a', 'b']) {
    test.describe(`variante ${v.toUpperCase()}`, () => {
        test.describe.configure({ mode: 'serial' });
        test.beforeAll(() => {
            execSync('npx tsx --env-file=.env.local scripts/seed.ts'); // base propre pour chaque variante
        });

        test('visiteur : catalogue public, rien d\'autre', async ({ page }) => {
            await page.goto(`/${v}/catalogue`);
            await expect(page.getByText('Germinal')).toBeVisible();
            await expect(page.locator('header nav a')).toHaveText(['Catalogue']);
            await expect(page.getByRole('button', { name: 'Emprunter' })).toHaveCount(0);
            await page.screenshot({ path: `e2e/captures/${v}-1-visiteur.png` });
        });

        test('adhérent : emprunte, suit, modifie son profil, ne décide pas', async ({ page, context }) => {
            await seConnecter(context, 'adherent_1:adherent');
            await page.goto(`/${v}/catalogue`);
            await expect(page.locator('header nav a')).toHaveText(['Catalogue', 'Emprunts', 'Mon profil']);
            await page.getByRole('listitem').filter({ hasText: 'Germinal' }).getByRole('button', { name: 'Emprunter' }).click();
            await expect(page.getByText('demande envoyée')).toBeVisible();
            await page.goto(`/${v}/emprunts`);
            await expect(page.getByRole('listitem').filter({ hasText: 'Germinal' })).toContainText('demandé');
            await page.getByRole('link', { name: 'Germinal' }).click();
            await expect(page.locator('dd').filter({ hasText: 'demandé' })).toBeVisible();
            await expect(page.locator('main').getByRole('button')).toHaveCount(0);
            await page.goto(`/${v}/profil`);
            await page.getByLabel('Téléphone').fill('06 11 22 33 44');
            await page.getByRole('button', { name: 'Enregistrer' }).click();
            await expect(page.getByText('Enregistré.')).toBeVisible();
            await page.screenshot({ path: `e2e/captures/${v}-2-adherent-profil.png` });
        });

        test('bibliothécaire : voit tout, décide selon le circuit', async ({ page, context }) => {
            await seConnecter(context, 'bibliothecaire_1:bibliothecaire');
            await page.goto(`/${v}/emprunts`);
            await expect(page.locator('header nav a')).toHaveText(['Catalogue', 'Emprunts']);
            await expect(page.getByRole('listitem').filter({ hasText: 'Germinal' })).toContainText('Adhérent adherent_1');
            await page.getByRole('link', { name: 'Germinal' }).click();
            await expect(page.locator('main').getByRole('button')).toHaveText(['Accepter', 'Refuser']);
            await page.screenshot({ path: `e2e/captures/${v}-3-bibliothecaire-decision.png` });
            await page.getByRole('button', { name: 'Accepter' }).click();
            await expect(page.locator('main').getByRole('button')).toHaveText(['Marquer rendu']);
            await expect(page.locator('dd').filter({ hasText: 'accepté' })).toBeVisible();
        });
    });
}
