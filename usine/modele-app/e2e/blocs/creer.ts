// BLOC « créer » (écran) : chaque fiche se CRÉE par son formulaire, par un rôle qui en a le droit, dans
// l'ordre où les fiches se désignent (la fiche désignée existe déjà quand on crée celle qui la désigne).
// (n° 54) Une LIGNE (fiche enfant) que d'autres fiches désignent est ajoutée ici aussi, à sa place dans cet ordre,
// par son vrai chemin (la page de son parent) : sinon la fiche qui la désigne n'avait rien à choisir (maintenance :
// l'intervention désigne un matériel installé, ligne d'un dossier client). Le bloc « enfants » la juge ensuite en entier.
import { expect, test } from '@playwright/test';
import { NOTICE, type NomFiche } from '../../lib/notice';
import { ajouterLigneParFormulaire, attendu, cellules, connectes, creerParFormulaire, etatAffiche, ouvrirPlusRecente,
    sectionLignes, seConnecter, toutesParOrdre } from '../noyau';

export function creer() {
    for (const [nom, fiche] of toutesParOrdre) {
        if (fiche.parent) {
            if (fiche.designee_par?.length) creerLigne(nom);
            continue;
        }
        if (!fiche.creation) continue;
        test(`création : ${fiche.libelle}`, async ({ page, context }) => {
            const createur = connectes.find((r) => attendu(r, nom, 'creer') && attendu(r, nom, 'voir'));
            test.skip(!createur, "aucun rôle connecté ne crée (et ne voit) cette fiche");
            await seConnecter(context, createur!);
            await page.goto(`/f/${nom}`);
            await expect(page.locator('main h1')).toBeVisible();
            const avant = await page.locator('main li').count();
            // (répétition temps 2) ce n'est plus « sauté » : une création permise mais impossible à l'écran
            // (rien à choisir) est un DÉFAUT — le saut cachait l'absence des profils des autres rôles
            expect(await creerParFormulaire(page, nom), `${createur} doit créer « ${fiche.libelle} » mais une fiche liée à choisir manque`).toBe(true);
            await expect(page.locator('main li')).toHaveCount(avant + 1);
        });
    }
}

function creerLigne(nom: NomFiche) {
    const fiche = NOTICE[nom];
    const parent = fiche.parent!.fiche as NomFiche;
    test(`création : ${fiche.libelle} (ligne, dans ${NOTICE[parent].libelle})`, async ({ browser }) => {
        // un rôle qui voit le parent et la ligne, et peut l'ajouter DANS L'ÉTAT actuel du parent (case de la ligne)
        let etatsPermis: string[] = [];
        for (const role of connectes.filter((r) => attendu(r, parent, 'voir') && attendu(r, nom, 'voir'))) {
            const cl = cellules.find((x) => x.actor === role && x.entity === nom);
            if (cl?.create !== 'yes') continue;
            const c = await browser.newContext();
            await seConnecter(c, role);
            const p = await c.newPage();
            await ouvrirPlusRecente(p, parent);
            const etat = await etatAffiche(p, parent);
            if (cl.create_while?.length && !(etat && cl.create_while.includes(etat))) {
                etatsPermis = cl.create_while; await c.close(); continue;
            }
            const s = sectionLignes(p, nom);
            await expect(s).toBeVisible();   // n'apparaît qu'une fois ses lignes chargées : compter avant donnerait 0
            const avant = await s.locator('li').count();
            expect(await ajouterLigneParFormulaire(s, nom, `Ligne désignée : ${fiche.libelle}`),
                `${role} doit ajouter « ${fiche.libelle} » mais une fiche liée à choisir manque`).not.toBeNull();
            await expect(s.locator('li')).toHaveCount(avant + 1);
            await c.close();
            return;
        }
        // dit clairement, pas caché : la fiche qui désigne cette ligne n'aura alors rien à choisir
        test.skip(true, etatsPermis.length
            ? `ligne ajoutable seulement plus tard dans le circuit du parent (${etatsPermis.join(', ')})`
            : "aucun rôle connecté n'ajoute (et ne voit) cette ligne");
    });
}
