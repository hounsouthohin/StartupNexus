// Tests d'ÉCRAN par rôle — code FIXE : chaque app reçoit ses propres tests, sans qu'on en écrive un seul.
// Les ATTENTES viennent de la matrice d'origine (verification/matrice.json), PAS de lib/droits.ts que
// lisent les écrans : si le traducteur se trompait dans les droits, l'écran et le test ne se
// tromperaient pas ensemble — le test échoue. Notice et menu ne servent qu'à trouver libellés et chemins.
import { expect, test, type BrowserContext } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { MENU, PROFIL } from '../lib/droits';
import { NOTICE, type NomFiche } from '../lib/notice';

type Cellule = { actor: string; entity: string; see: string; create: string; transitions: Record<string, string[]> };
const cellules: Cellule[] = JSON.parse(readFileSync(resolve('verification/matrice.json'), 'utf8')).cells;

function attendu(role: string, fiche: string, action: 'voir' | 'creer' | `etat:${string}`, etat?: string): boolean {
    const c = cellules.find((x) => x.actor === role && x.entity === fiche);
    if (!c) return false;
    if (action === 'voir') return c.see !== 'none';
    if (action === 'creer') return c.create === 'yes';
    return !!etat && !!c.transitions[etat]?.includes(action.slice(5));
}

const BASE = process.env.BASE_URL ?? 'http://localhost:3300';
const roles = [...new Set(cellules.map((c) => c.actor))];
const connectes = roles.filter((r) => r !== 'visitor');
const seConnecter = (context: BrowserContext, role: string) =>
    role === 'visitor' ? Promise.resolve() : context.addCookies([{ name: 'session_usine', value: `${role}_1:${role}`, url: BASE }]);

test.describe.configure({ mode: 'serial' });

// 0. Chaque fiche de la matrice a son entrée de menu (sinon aucun rôle ne pourrait l'atteindre)
test('menu : une entrée par fiche de la matrice', () => {
    expect(MENU.map((m) => m.fiche).sort()).toEqual([...new Set(cellules.map((c) => c.entity))].sort());
});

// 1. Chaque rôle : son menu, et les boutons de création qu'il doit (ou ne doit pas) voir
for (const role of roles) {
    test(`${role} : menu et boutons de création`, async ({ page, context }) => {
        await seConnecter(context, role);
        await page.goto('/');
        await expect(page.locator('header nav a')).toHaveText(MENU.filter((m) => attendu(role, m.fiche, 'voir')).map((m) => m.libelle));
        for (const m of MENU.filter((x) => x.chemin.startsWith('/f/') && attendu(role, x.fiche, 'voir'))) {
            await page.goto(m.chemin);
            await expect(page.locator('main h1')).toHaveText(NOTICE[m.fiche].titre);
            if (!(await page.locator('main li').count())) continue; // liste vide : rien à juger
            for (const a of NOTICE[m.fiche].actionsLigne ?? []) {
                const boutons = page.getByRole('button', { name: a.libelle });
                if (attendu(role, a.cree, 'creer')) await expect(boutons.first()).toBeVisible();
                else await expect(boutons).toHaveCount(0);
            }
        }
    });
}

// 2. Chaque circuit : l'initiateur crée par l'écran ; chaque rôle voit les boutons de SA décision
for (const [nom, fiche] of Object.entries(NOTICE) as [NomFiche, (typeof NOTICE)[NomFiche]][]) {
    if (!fiche.etat) continue;
    const etat = fiche.etat;
    const source = (Object.entries(NOTICE) as [NomFiche, (typeof NOTICE)[NomFiche]][])
        .find(([, f]) => f.actionsLigne?.some((a) => a.cree === nom));
    test(`circuit : ${fiche.libelle}`, async ({ browser }) => {
        test.skip(!source, "pas de création par l'écran pour cette fiche (formulaire de création : N1.5)");
        const [nomSource, ficheSource] = source!;
        const action = ficheSource.actionsLigne!.find((a) => a.cree === nom)!;
        const createur = connectes.find((r) => attendu(r, nom, 'creer'))!;
        const c1 = await browser.newContext();
        await seConnecter(c1, createur);
        const p1 = await c1.newPage();
        await p1.goto(`/f/${nomSource}`);
        await p1.getByRole('button', { name: action.libelle }).first().click();
        await expect(p1.getByText('demande enregistrée')).toBeVisible();
        await c1.close();
        for (const role of connectes.filter((r) => attendu(r, nom, 'voir'))) {
            const c = await browser.newContext();
            await seConnecter(c, role);
            const p = await c.newPage();
            await p.goto(`/f/${nom}`);
            await p.locator('main li a').first().click(); // la plus récente (tri par date décroissante)
            await expect(p.locator('dd').filter({ hasText: etat.libelles[etat.initial] })).toBeVisible();
            const attendus = Object.entries(etat.boutons)
                .filter(([cible]) => attendu(role, nom, `etat:${cible}`, etat.initial)).map(([, libelle]) => libelle);
            await expect(p.locator('main section button')).toHaveText(attendus);
            if (attendus.length) {
                const [cible] = Object.entries(etat.boutons).find(([, libelle]) => libelle === attendus[0])!;
                await p.getByRole('button', { name: attendus[0] }).click();
                await expect(p.locator('dd').filter({ hasText: etat.libelles[cible] })).toBeVisible();
            }
            await c.close();
        }
    });
}

// 3. Le profil : la personne le modifie et l'enregistre
test('profil : modifier et enregistrer', async ({ page, context }) => {
    test.skip(!PROFIL, 'pas de profil dans cette app');
    const champ = NOTICE[PROFIL!.fiche].modifiables.find((c) => c.saisie === 'texte' && c.obligatoire);
    test.skip(!champ, 'aucun champ texte à modifier');
    await seConnecter(context, PROFIL!.role);
    await page.goto('/profil');
    await page.getByLabel(champ!.libelle).fill('Modifié par le test');
    await page.getByRole('button', { name: 'Enregistrer' }).click();
    await expect(page.getByText('Enregistré.')).toBeVisible();
});
