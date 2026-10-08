// Base propre + catalogue de démo (client sans règles). Usage : npx tsx --env-file=.env.local scripts/seed.ts
import { rawDb } from '../lib/db';

async function main() {
    await rawDb.borrowing.deleteMany();
    await rawDb.member.deleteMany();
    await rawDb.book.deleteMany();
    for (const [title, author] of [
        ['Germinal', 'Émile Zola'],
        ['Le Petit Prince', 'Antoine de Saint-Exupéry'],
        ['Une si longue lettre', 'Mariama Bâ'],
        ["L'Étranger", 'Albert Camus'],
    ])
        await rawDb.book.create({ data: { title, author } });
    console.log('4 ouvrages, aucun emprunt, aucun profil');
    process.exit(0);
}
main();
