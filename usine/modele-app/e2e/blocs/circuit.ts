// BLOC « circuit » (écran) : une fiche à l'état de départ — créée d'un clic par son initiateur, ou la plus
// récente (créée par le formulaire, ou donnée de départ) ; le circuit est PARCOURU état après état et
// chaque rôle voit SA décision. (Trou trouvé par la répétition générale : les circuits des registres
// n'étaient jamais essayés ; à la répétition temps 2 : seule la 1re étape l'était.)
import { expect, test } from '@playwright/test';
import { attendu, champEtat, connectes, fiches, seConnecter } from '../noyau';

export function circuit() {
    for (const [nom, fiche] of fiches) {
        if (!fiche.etat) continue;
        const etat = fiche.etat;
        const source = fiches.find(([, f]) => f.actionsLigne?.some((a) => a.cree === nom));
        test(`circuit : ${fiche.libelle}`, async ({ browser }) => {
            const ouvrirListe = async (role: string) => {
                const c = await browser.newContext();
                await seConnecter(c, role);
                const p = await c.newPage();
                await p.goto(`/f/${nom}`);
                await expect(p.locator('main h1')).toBeVisible();
                return { c, p };
            };
            if (source) {
                const [nomSource, ficheSource] = source;
                const action = ficheSource.actionsLigne!.find((a) => a.cree === nom)!;
                const createur = connectes.find((r) => attendu(r, nom, 'creer'))!;
                const c1 = await browser.newContext();
                await seConnecter(c1, createur);
                const p1 = await c1.newPage();
                await p1.goto(`/f/${nomSource}`);
                await p1.getByRole('button', { name: action.libelle }).first().click();
                await expect(p1.getByText('demande enregistrée')).toBeVisible();
                await c1.close();
            } else {
                const voit = connectes.find((r) => attendu(r, nom, 'voir'));
                test.skip(!voit, 'aucun rôle connecté ne voit cette fiche');
                const { c, p } = await ouvrirListe(voit!);
                const existe = await p.locator('main li a').count();
                await c.close();
                test.skip(!existe, 'aucune fiche à ouvrir');
            }
            const ouvrir = async (role: string) => {
                const { c, p } = await ouvrirListe(role);
                await p.locator('main li a').first().click(); // la plus récente (tri par date décroissante)
                return { c, p };
            };
            const aDesEtapes = (s: string) => connectes.some((r) => Object.keys(etat.boutons).some((cible) => attendu(r, nom, `etat:${cible}`, s)));
            const voient = connectes.filter((r) => attendu(r, nom, 'voir'));
            const vus = new Set<string>();
            let actuel = etat.initial;
            while (!vus.has(actuel)) {
                vus.add(actuel);
                const choix: { role: string; libelle: string; cible: string }[] = [];
                for (const role of voient) {
                    const { c, p } = await ouvrir(role);
                    await expect(champEtat(p)).toHaveText(etat.libelles[actuel]);   // texte exact, champ « État » seul (n° 55)
                    // affordance honnête : deux boutons de la page ne portent jamais le même nom (« Supprimer » l'étape
                    // et « Supprimer » la fiche — trouvé à la répétition temps 2)
                    // (les boutons d'une LIGNE de tableau — « Retirer » sur chaque ligne — font le même geste sur
                    // des lignes différentes : ils ne comptent pas)
                    const noms = (await p.locator('main button:visible').evaluateAll((els) =>
                        els.filter((e) => !e.closest('li')).map((e) => (e.textContent ?? '').trim()))).filter(Boolean);
                    expect(noms.filter((n, i) => noms.indexOf(n) !== i), `${role} : deux boutons portent le même nom`).toEqual([]);
                    const permis = Object.entries(etat.boutons).filter(([cible]) => attendu(role, nom, `etat:${cible}`, actuel));
                    // :visible — Next garde la page précédente CACHÉE pour le retour arrière (ses boutons ne
                    // comptent pas) ; data-bloc : seulement les boutons de DÉCISION
                    await expect(p.locator('[data-bloc="decision"] button:visible')).toHaveText(permis.map(([, libelle]) => libelle));
                    choix.push(...permis.map(([cible, libelle]) => ({ role, cible, libelle })));
                    await c.close();
                }
                if (!choix.length) break;
                // … puis UN rôle qui en a le droit décide (de préférence vers un état pas encore vu qui a lui-même
                // des étapes), et l'état change à l'écran
                const d = choix.find((x) => !vus.has(x.cible) && aDesEtapes(x.cible)) ?? choix.find((x) => !vus.has(x.cible)) ?? choix[0];
                const { c, p } = await ouvrir(d.role);
                await p.locator('[data-bloc="decision"]').getByRole('button', { name: d.libelle, exact: true }).click();
                await expect(champEtat(p)).toHaveText(etat.libelles[d.cible]);
                await c.close();
                actuel = d.cible;
            }
        });
    }
}
