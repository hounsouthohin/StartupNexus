// BLOC « profil » (écran) : chaque profil (un par rôle) — la personne ouvre LE SIEN ; elle le modifie si la
// matrice le permet, sinon il est en lecture seule (pas de bouton « Enregistrer » qui serait refusé).
import { expect, test } from '@playwright/test';
import { PROFILS } from '../../lib/droits';
import { NOTICE } from '../../lib/notice';
import { attendu, seConnecter } from '../noyau';

export function profil() {
    for (const p of PROFILS) {
        test(`profil : ${NOTICE[p.fiche].libelle} — ouvrir, modifier si permis`, async ({ page, context }) => {
            await seConnecter(context, p.role);
            await page.goto('/profil');
            await expect(page.locator('main h1')).toHaveText(`Mon ${NOTICE[p.fiche].libelle}`);
            if (!attendu(p.role, p.fiche, 'modifier')) {
                await expect(page.getByRole('button', { name: 'Enregistrer' })).toHaveCount(0);
                return;
            }
            const champ = NOTICE[p.fiche].modifiables.find((c) => c.saisie === 'texte' && c.obligatoire);
            test.skip(!champ, 'aucun champ texte à modifier');
            await page.getByLabel(champ!.libelle, { exact: true }).fill('Modifié par le test');
            await page.getByRole('button', { name: 'Enregistrer' }).click();
            await expect(page.getByText('Enregistré.')).toBeVisible();
        });
    }
}
