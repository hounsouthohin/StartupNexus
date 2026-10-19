// BLOC « enfants » (écran, N1.3) : les LIGNES d'une fiche, dans la page de leur parent. Pour chaque sorte de
// ligne : chaque rôle qui voit le parent voit la section ; le bouton « Ajouter » si et seulement si la case de la
// ligne le permet DANS L'ÉTAT du parent ; un rôle qui en a le droit ajoute une ligne
// (elle apparaît), la modifie, la retire (après confirmation).
import { expect, test, type Page } from '@playwright/test';
import { NOTICE, type NomFiche } from '../../lib/notice';
import { ajouterLigneParFormulaire, attendu, cellules, connectes, etatAffiche, ouvrirPlusRecente, sectionLignes, seConnecter, toutesParOrdre } from '../noyau';

// joué deux fois : AVANT les décisions des circuits (le parent est dans son état de départ, où ses lignes se gèrent
// souvent) et APRÈS (il a avancé : là où elles ne se gèrent plus, « Ajouter » doit disparaître — sans ce 2e passage,
// une pièce qui oublierait l'état du parent passerait inaperçue)
export function enfants(moment: string) {
    for (const [nom, fiche] of toutesParOrdre) {
        if (!fiche.parent) continue;
        const parent = fiche.parent.fiche as NomFiche;
        test(`lignes (${moment}) : ${fiche.libelle} (dans ${NOTICE[parent].libelle})`, async ({ browser }) => {
            const section = (p: Page) => sectionLignes(p, nom);
            const ajouter = `Ajouter : ${fiche.libelle}`;
            let gestionnaire: string | undefined;
            let vu = false;
            for (const role of connectes.filter((r) => attendu(r, parent, 'voir'))) {
                const c = await browser.newContext();
                await seConnecter(c, role);
                const p = await c.newPage();
                await p.goto(`/f/${parent}`);
                await expect(p.locator('main h1')).toBeVisible();
                if (!(await p.locator('main li a').count())) { await c.close(); continue; }
                vu = true;
                await ouvrirPlusRecente(p, parent);
                const etat = await etatAffiche(p, parent);
                const voitLignes = attendu(role, nom, 'voir');
                await expect(section(p)).toHaveCount(voitLignes ? 1 : 0);
                if (voitLignes) {
                    // ajouter une ligne : selon la case de la LIGNE dans la matrice (create, create_while : états du
                    // parent), dans l'état actuel du parent
                    const cl = cellules.find((x) => x.actor === role && x.entity === nom);
                    const permis = cl?.create === 'yes' && (!cl.create_while?.length || (!!etat && cl.create_while.includes(etat)));
                    const b = section(p).getByRole('button', { name: ajouter, exact: true });
                    if (permis) { await expect(b).toBeVisible(); gestionnaire ??= role; } else await expect(b).toHaveCount(0);
                }
                await c.close();
            }
            test.skip(!vu, 'aucun parent à ouvrir');
            if (!gestionnaire) return;
            // un rôle qui gère : ajoute une ligne, la modifie, la retire
            const c = await browser.newContext();
            await seConnecter(c, gestionnaire);
            const p = await c.newPage();
            await ouvrirPlusRecente(p, parent);
            const s = section(p);
            // (n° 54) la section n'apparaît qu'une fois ses lignes chargées : compter avant donnait 0 (invisible tant
            // qu'aucune ligne n'existait d'avance ; le bloc « créer » en ajoute maintenant une)
            await expect(s).toBeVisible();
            // ajoute une ligne par son formulaire (le 1er champ texte reçoit `marque`) ; renvoie true si elle est marquée
            const ajouterLigne = async (marque: string): Promise<boolean> => {
                const marquee = await ajouterLigneParFormulaire(s, nom, marque);
                // une ligne permise mais impossible à ajouter (rien à choisir) est un DÉFAUT, dit clairement (règle du n° 39)
                expect(marquee, `${gestionnaire} doit ajouter « ${fiche.libelle} » mais une fiche liée à choisir manque`).not.toBeNull();
                return !!marquee;
            };
            const avant = await s.locator('li').count();
            // (n° 57) une marque PAR PASSAGE : la ligne du 1er passage reste quand on n'a pas le droit de la retirer
            // (l'agent ajoute des photos, ne les retire pas) — même marque au 2e passage → deux lignes « la » ligne
            const marque = `Ligne d'essai (${moment}) : ${fiche.libelle}`;
            const marquee = await ajouterLigne(marque);
            await expect(s.locator('li')).toHaveCount(avant + 1);
            const ligne = marquee ? s.locator('li', { hasText: marque }) : s.locator('li').last();
            await expect(ligne).toHaveCount(1);
            if (attendu(gestionnaire, nom, 'supprimer', await etatAffiche(p, parent))) {
                await ligne.getByRole('button', { name: 'Retirer', exact: true }).click();
                await ligne.getByRole('button', { name: 'Confirmer le retrait', exact: true }).click();
                await expect(s.locator('li')).toHaveCount(avant);
                // (13 oct) d'autres fiches désignent ces lignes (les points de checklist d'un type d'intervention) : on en
                // laisse une, sinon les tests suivants n'auraient rien à choisir — le juge ne crée pas lui-même l'impossible
                if (fiche.designee_par?.length) {
                    await ajouterLigne(`Ligne gardée : ${fiche.libelle}`);
                    await expect(s.locator('li')).toHaveCount(avant + 1);
                }
            }
            await c.close();
        });
    }
}
