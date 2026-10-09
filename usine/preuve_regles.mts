// PREUVE que le testeur des règles attrape les erreurs, sur une app FABRIQUÉE. Même méthode que
// l'étude 04 (poc/regles/mutate.ts, dont la fabrique d'erreurs est reprise telle quelle) : UNE erreur à
// la fois dans les règles du schéma, on relance le testeur livré avec l'app, il doit la signaler.
// Un « survivant » est soit un trou du testeur, soit une erreur sans effet : à examiner un par un.
// Les erreurs ne touchent que les règles, jamais les tables : la base de l'app sert telle quelle.
// Usage, depuis le dossier de l'app : npx tsx <chemin>/usine/preuve_regles.mts
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';

type Mutant = { line: number; operator: string; description: string; source: string; mutatedLine: string };

// ─── Lecture d'une règle @@allow / @@deny : où commence et finit sa condition ─────────────
// (petit lecteur qui suit les parenthèses et les guillemets ; pas d'expression régulière)
function conditionBounds(line: string): { start: number; end: number } | null {
    const at = line.includes('@@allow(') ? line.indexOf('@@allow(') : line.indexOf('@@deny(');
    if (at < 0 || line.trimStart().startsWith('//')) return null;
    let i = line.indexOf('(', at) + 1;
    while (line[i] === ' ') i++;
    if (line[i] !== "'") return null;
    i = line.indexOf("'", i + 1) + 1; // fin de l'opération ('read', 'create'…)
    i = line.indexOf(',', i) + 1;
    const start = i;
    let depth = 0;
    let quoted = false;
    for (let j = start; j < line.length; j++) {
        const ch = line[j];
        if (ch === "'") quoted = !quoted;
        if (quoted) continue;
        if (ch === '(' || ch === '[') depth++;
        else if (ch === ')' || ch === ']') {
            if (depth === 0) return { start, end: j };
            depth--;
        }
    }
    return null;
}

// Découpe une condition sur les « && » de premier niveau.
function topLevelAnd(cond: string): string[] {
    const parts: string[] = [];
    let depth = 0;
    let quoted = false;
    let from = 0;
    for (let j = 0; j < cond.length; j++) {
        const ch = cond[j];
        if (ch === "'") quoted = !quoted;
        if (quoted) continue;
        if (ch === '(' || ch === '[') depth++;
        else if (ch === ')' || ch === ']') depth--;
        else if (depth === 0 && cond.startsWith('&&', j)) {
            parts.push(cond.slice(from, j).trim());
            from = j + 2;
        }
    }
    parts.push(cond.slice(from).trim());
    return parts;
}

// ─── Fabrication des mutants : 3 sortes d'erreurs ──────────────────────────────────────────
function mutants(source: string): Mutant[] {
    const lines = source.split('\n');
    const out: Mutant[] = [];
    const seen = new Set<string>();
    const add = (n: number, operator: string, description: string, newLine: string | null) => {
        const copy = [...lines];
        if (newLine === null) copy.splice(n, 1);
        else copy[n] = newLine;
        const src = copy.join('\n');
        if (src === source || seen.has(src)) return;
        seen.add(src);
        out.push({ line: n + 1, operator, description, source: src, mutatedLine: newLine ?? '(ligne supprimée)' });
    };
    lines.forEach((line, n) => {
        const b = conditionBounds(line);
        if (!b) return;
        // 1. oublier une règle entière
        add(n, 'supprimer', 'règle supprimée', null);
        // 2. ouvrir à tout connecté une condition de rôle
        let k = line.indexOf("auth().role == '");
        while (k >= 0) {
            const end = line.indexOf("'", k + "auth().role == '".length) + 1;
            add(n, 'élargir', `« ${line.slice(k, end)} » remplacé par « auth() != null »`,
                line.slice(0, k) + 'auth() != null' + line.slice(end));
            k = line.indexOf("auth().role == '", end);
        }
        // 3. oublier une des conditions (« && ») de la règle
        const cond = line.slice(b.start, b.end);
        const parts = topLevelAnd(cond);
        if (parts.length >= 2)
            parts.forEach((p, i) => {
                const kept = parts.filter((_, j) => j !== i).join(' && ');
                add(n, 'oublier une condition', `condition « ${p} » retirée`,
                    line.slice(0, b.start) + ' ' + kept + line.slice(b.end));
            });
    });
    return out;
}

// ─── Exécution ─────────────────────────────────────────────────────────────────────────────
const SCHEMA = 'zenstack/schema.zmodel';
const original = readFileSync(SCHEMA, 'utf8');
const list = mutants(original.replace(/\r\n/g, '\n'));
const generer = () => spawnSync('npx zen generate --schema zenstack/schema.zmodel -o zenstack --silent', { shell: true, encoding: 'utf8' });
const tester = () => spawnSync('npx tsx --env-file=.env.local verification/testeur.mts', { shell: true, encoding: 'utf8', timeout: 300_000 });
type Result = Mutant & { verdict: 'tué' | 'survivant' | 'invalide' | 'plantage'; detail: string };
const results: Result[] = [];
console.log(`▶ ${list.length} mutants`);

try {
    list.forEach((m, i) => {
        writeFileSync(SCHEMA, m.source);
        const gen = generer();
        let verdict: Result['verdict'];
        let detail = '';
        if (gen.status !== 0) {
            verdict = 'invalide';
            detail = (gen.stderr || gen.stdout).split('\n').find((l) => l.trim()) ?? '';
        } else {
            const run = tester();
            const lines = (run.stdout ?? '').split('\n');
            const summary = lines.find((l) => l.includes('conformes à la matrice'));
            if (!summary) {
                verdict = 'plantage';
                detail = ((run.stderr ?? '') + (run.stdout ?? '')).split('\n').find((l) => l.includes('Error')) ?? 'pas de bilan';
            } else {
                const [okCount, total] = summary.trim().split(' ')[0].split('/').map(Number);
                verdict = okCount === total ? 'survivant' : 'tué';
                detail = verdict === 'tué' ? (lines.find((l) => l.trim().startsWith('•')) ?? '').trim() : summary.trim();
            }
        }
        results.push({ ...m, verdict, detail });
        console.log(`  ${verdict.padEnd(10)} ${String(i + 1).padStart(3, '0')}  l.${m.line}  ${m.operator} — ${m.description}`);
    });
} finally {
    writeFileSync(SCHEMA, original); // l'app retrouve ses vraies règles
    generer();
}

// ─── Rapport ───────────────────────────────────────────────────────────────────────────────
const count = (v: Result['verdict']) => results.filter((r) => r.verdict === v).length;
const valid = results.length - count('invalide');
const killed = count('tué');
const rate = valid ? Math.round((1000 * killed) / valid) / 10 : 0;
const report = [
    '# Mutants — règles de l\'app fabriquée',
    '',
    `${results.length} mutants · ${count('invalide')} invalides (le schéma ne compile plus) · ${valid} valides`,
    `**Tués : ${killed}/${valid} (${rate} %)** · survivants : ${count('survivant')} · plantages : ${count('plantage')}`,
    '',
    '## Survivants et plantages (à examiner)',
    '',
    ...results
        .filter((r) => r.verdict === 'survivant' || r.verdict === 'plantage')
        .map((r) => `- **${r.verdict}** l.${r.line} — ${r.operator} : ${r.description}\n  \`${r.mutatedLine.trim()}\`\n  ${r.detail}`),
    '',
    '## Tous les mutants',
    '',
    ...results.map((r) => `- ${r.verdict} · l.${r.line} · ${r.operator} · ${r.description} — ${r.detail}`),
].join('\n');
writeFileSync('../logs/preuve-regles.md', report);
// (N1.1b) le même résultat, lisible par programme (la carte des blocs en tire le score de chaque bloc) :
// pour chaque mutant, la règle d'origine qu'il abîme
const lignesOrigine = original.replace(/\r\n/g, '\n').split('\n');
writeFileSync('../preuve-regles.json', JSON.stringify(results.map((r) => ({
    ligne: r.line, regle: lignesOrigine[r.line - 1].trim(), operateur: r.operator, description: r.description, verdict: r.verdict,
})), null, 1));
console.log(`\n  Tués ${killed}/${valid} (${rate} %) · survivants ${count('survivant')} · invalides ${count('invalide')} · plantages ${count('plantage')}`);
