// BLOC « menu » (écran) : chaque fiche a son entrée ; chaque rôle a SON menu, le bouton « Nouveau… » de
// chaque liste où il crée, et les boutons de création d'un clic.
import { expect, test } from '@playwright/test';
import { MENU, pourRole, type Role } from '../../lib/droits';
import { NOTICE } from '../../lib/notice';
import { attendu, fichesDeLaMatrice, roles, seConnecter } from '../noyau';

export function menu() {
    // chaque fiche de la matrice a son entrée de menu (sinon aucun rôle ne pourrait l'atteindre)
    test('menu : une entrée par fiche de la matrice', () => {
        expect([...new Set(MENU.map((m) => m.fiche))].sort()).toEqual([...fichesDeLaMatrice].sort());
    });

    for (const role of roles) {
        test(`${role} : menu et boutons de création`, async ({ page, context }) => {
            await seConnecter(context, role);
            await page.goto('/');
            const entrees = MENU.filter((m) => attendu(role, m.fiche, 'voir') && pourRole(m, role as Role));   // « Mon … » : seulement son rôle
            await expect(page.locator('header nav a')).toHaveText(entrees.map((m) => m.libelle));
            for (const m of entrees.filter((x) => x.chemin.startsWith('/f/'))) {
                await page.goto(m.chemin);
                await expect(page.locator('main h1')).toHaveText(NOTICE[m.fiche].titre);
                const nouveau = NOTICE[m.fiche].creation?.libelle;
                if (nouveau) {
                    const b = page.getByRole('button', { name: nouveau, exact: true });
                    if (attendu(role, m.fiche, 'creer')) await expect(b).toBeVisible();
                    else await expect(b).toHaveCount(0);
                }
                if (!(await page.locator('main li').count())) continue; // liste vide : pas de boutons de ligne à juger
                for (const a of NOTICE[m.fiche].actionsLigne ?? []) {
                    const boutons = page.getByRole('button', { name: a.libelle });
                    if (attendu(role, a.cree, 'creer')) await expect(boutons.first()).toBeVisible();
                    else await expect(boutons).toHaveCount(0);
                }
            }
        });
    }
}
