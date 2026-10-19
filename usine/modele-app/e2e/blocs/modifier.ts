// BLOC « modifier » (écran) : chaque rôle qui voit la fiche a le bouton « Modifier » si et seulement si la
// matrice le permet DANS SON ÉTAT ; un rôle qui en a le droit modifie, et l'écran le montre.
import { expect, test } from '@playwright/test';
import { NOTICE, type NomFiche } from '../../lib/notice';
import { attendu, connectes, etatAffiche, fiches, ouvrirPlusRecente, seConnecter } from '../noyau';

export function modifier() {
    for (const [nom, fiche] of fiches) {
        if (!fiche.creation) continue;
        test(`modifier : ${fiche.libelle}`, async ({ browser }) => {
            let editeur: string | undefined;
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
                const permis = attendu(role, nom, 'modifier', await etatAffiche(p, nom));
                const b = p.getByRole('button', { name: 'Modifier', exact: true });
                if (permis) { await expect(b).toBeVisible(); editeur ??= role; } else await expect(b).toHaveCount(0);
                await c.close();
            }
            test.skip(!vu, 'aucune fiche à ouvrir');
            const champ = fiche.modifiables.find((c) => c.saisie === 'texte');
            if (!editeur || !champ) return;
            const c = await browser.newContext();
            await seConnecter(c, editeur);
            const p = await c.newPage();
            await ouvrirPlusRecente(p, nom);
            // une valeur PROPRE à cette fiche, vérifiée sous SON intitulé (fausse alarme trouvée sur l'union :
            // une même valeur, écrite dans des fiches liées, s'affichait trois fois)
            const valeur = `Modifié : ${fiche.libelle}`;
            // (N1.3, défaut intermittent trouvé par le témoin d'une preuve) les listes de choix des liens sont
            // RALENTIES exprès et « Enregistrer » est cliqué aussitôt : le formulaire doit attendre (« Patientez »),
            // jamais partir avec un lien vide — le cas qui n'arrivait qu'au hasard est joué à chaque fois
            const cibles = (fiche.liens ?? []).filter((l) => !l.proprietaire && !l.parent).map((l) => NOTICE[l.cible as NomFiche].modele);
            const lent = new RegExp(`/api/model/(${cibles.join('|')})/findMany`);
            if (cibles.length) await p.route(lent, async (r) => { await new Promise((ok) => setTimeout(ok, 1500)); await r.continue(); });
            await p.getByRole('button', { name: 'Modifier', exact: true }).click();
            await p.locator(`main form [name="${champ.nom}"]`).fill(valeur);
            if (cibles.length) {
                await p.locator('main form').getByRole('button', { name: 'Enregistrer' }).click();
                await expect(p.locator('main form').getByText('Patientez')).toBeVisible();
                await expect(p.locator('main form').getByText(/^Refusé/)).toHaveCount(0);
                await p.unroute(lent);
                await expect(p.locator('main form [data-chargement]')).toHaveCount(0);
            }
            await p.locator('main form').getByRole('button', { name: 'Enregistrer' }).click();
            await expect(p.locator('main form')).toHaveCount(0);
            await expect(p.locator('dl').getByText(champ.libelle, { exact: true }).locator('xpath=following-sibling::dd[1]')).toHaveText(valeur);
            await c.close();
        });
    }
}
