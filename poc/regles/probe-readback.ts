// Sonde E4 : quand ZenStack refuse de RELIRE le résultat d'une écriture, l'écriture est-elle annulée ?
// Utilise le mutant notes-frais-044 (règle « propriétaire immuable » supprimée) et notes-frais-010
// (création « au nom d'un autre » autorisée). Usage : npx tsx probe-readback.ts
import { ORMError, ZenStackClient } from '@zenstackhq/orm';
import { PostgresDialect } from '@zenstackhq/orm/dialects/postgres';
import { PolicyPlugin } from '@zenstackhq/plugin-policy';
import { readFileSync } from 'node:fs';
import { Pool } from 'pg';

const url = readFileSync('cases/notes-frais/gen/database-url.txt', 'utf8').trim();
for (const mutant of ['notes-frais-044', 'notes-frais-010']) {
    const { schema } = await import(`./cases/_mutants/${mutant}/gen/schema.ts`);
    const raw: any = new ZenStackClient(schema, { dialect: new PostgresDialect({ pool: new Pool({ connectionString: url }) }) });
    const emp1 = raw.$use(new PolicyPlugin()).$setAuth({ id: 'employee_1', role: 'employee' });
    await raw.expenseReport.deleteMany();
    const r = await raw.expenseReport.create({ data: { label: 'Train', amount: 10, ownerId: 'employee_1' } });

    let outcome = 'PERMIS';
    try {
        if (mutant.endsWith('044'))
            await emp1.expenseReport.update({ where: { id: r.id }, data: { ownerId: 'employee_2' } });
        else await emp1.expenseReport.create({ data: { label: 'Faux', amount: 1, ownerId: 'employee_2' } });
    } catch (e) {
        outcome = `REFUSÉ (${e instanceof ORMError ? e.reason : 'autre'} : ${(e as Error).message.split('\n')[0]})`;
    }
    const rows = await raw.expenseReport.findMany({ select: { label: true, ownerId: true } });
    console.log(`\n${mutant} — réponse : ${outcome}`);
    console.log(`  en base après coup : ${JSON.stringify(rows)}`);
}
process.exit(0);
