// BLOC « supprimer » (écran) : le bouton « Supprimer » si et seulement si la matrice le permet dans l'état
// de la fiche ; une fiche utilisée a son bouton grisé avec la raison (intégrité) ; un rôle qui en a le
// droit supprime (après confirmation), et la fiche disparaît.
import { expect, test } from '@playwright/test';
import { attendu, connectes, creerParFormulaire, etatAffiche, fiches, ouvrirPlusRecente, seConnecter } from '../noyau';

export function supprimer() {
    for (const [nom, fiche] of fiches) {
        if (!fiche.creation) continue;
        test(`supprimer : ${fiche.libelle}`, async ({ browser }) => {
            let supprimeur: string | undefined;
            let vu = false;
            for (const role of connectes.filter((r) => attendu(r, nom, 'voir'))) {
                const c = await browser.newContext();
                await seConnecter(c, role);
                const p = await c.newPage();
                await p.goto(`/f/${nom}`);
                await expect(p.locator('main h1')).toBeVisible();
                if (!(await p.locator('main li a').count())) { await c.close(); continue; }
                vu = true;
                await ouvrirPlusRecente(p, nom);
                const permis = attendu(role, nom, 'supprimer', await etatAffiche(p, nom));
                const b = p.getByRole('button', { name: 'Supprimer', exact: true });
                if (permis) { await expect(b).toBeVisible(); supprimeur ??= role; } else await expect(b).toHaveCount(0);
                await c.close();
            }
            test.skip(!vu, 'aucune fiche à ouvrir');
            if (!supprimeur) return;
            const c = await browser.newContext();
            await seConnecter(c, supprimeur);
            const p = await c.newPage();
            await p.goto(`/f/${nom}`);
            await expect(p.locator('main h1')).toBeVisible();
            // (a) une fiche UTILISÉE (désignée par d'autres) : bouton grisé et raison affichée (intégrité)
            await ouvrirPlusRecente(p, nom);
            if (attendu(supprimeur, nom, 'supprimer', await etatAffiche(p, nom)) && (await p.getByText('impossible de la supprimer').count()))
                await expect(p.getByRole('button', { name: 'Supprimer', exact: true })).toBeDisabled();
            // (b) une VRAIE suppression, sur une fiche neuve que rien ne désigne (créée par le formulaire,
            // repérée par un nom unique) — sinon la plus récente, si elle est libre
            const texte = fiche.modifiables.find((x) => x.saisie === 'texte');
            const marque = `À supprimer : ${fiche.libelle}`;
            await p.goto(`/f/${nom}`);
            await expect(p.locator('main h1')).toBeVisible();
            const neuve = !!texte && attendu(supprimeur, nom, 'creer') && (await creerParFormulaire(p, nom, marque));
            // la LIGNE qui contient le nom unique, puis son lien (le lien n'est pas forcément le nom : fausse
            // alarme trouvée sur l'union)
            const ligneNeuve = () => p.locator('main li:visible', { hasText: marque }).first().locator('a').first();
            if (neuve) await ligneNeuve().click();
            else await ouvrirPlusRecente(p, nom);
            await expect(p.locator('dl')).toBeVisible();
            if (!attendu(supprimeur, nom, 'supprimer', await etatAffiche(p, nom)) || (await p.getByText('impossible de la supprimer').count())) {
                await c.close();
                return;    // pas supprimable dans cet état, ou utilisée : jugé en (a)
            }
            await p.goto(`/f/${nom}`);
            await expect(p.locator('main h1')).toBeVisible();     // la liste est chargée AVANT de compter
            const avant = await p.locator('main li:visible').count();
            if (neuve) await ligneNeuve().click();
            else await ouvrirPlusRecente(p, nom);
            await p.getByRole('button', { name: 'Supprimer', exact: true }).click();
            await p.getByRole('button', { name: 'Confirmer la suppression' }).click();
            await expect(p).toHaveURL(new RegExp(`/f/${nom}$`));
            await expect(p.locator('main li:visible')).toHaveCount(avant - 1);
            if (neuve) await expect(p.locator('main li:visible', { hasText: marque })).toHaveCount(0);
            await c.close();
        });
    }
}
