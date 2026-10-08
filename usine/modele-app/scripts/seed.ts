// Données de départ (depart.json, produit par l'usine) ; vide d'abord la base dans le bon ordre.
// Client SANS règles. Usage : npx tsx --env-file=.env.local scripts/seed.ts
import { readFileSync } from 'node:fs';
import { rawDb } from '../lib/db';

type Depart = { suppression: string[]; creation: string[]; donnees: Record<string, Record<string, unknown>[]> };
const depart: Depart = JSON.parse(readFileSync(new URL('../depart.json', import.meta.url), 'utf8'));
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const db = rawDb as any;

async function main() {
    for (const m of depart.suppression) await db[m].deleteMany();
    let n = 0;
    for (const m of depart.creation)
        for (const ligne of depart.donnees[m] ?? []) {
            await db[m].create({ data: ligne });
            n++;
        }
    console.log(`base vidée ; ${n} fiche(s) de départ créée(s)`);
    process.exit(0);
}
main().catch((e) => {
    console.error(e);
    process.exit(1);
});
