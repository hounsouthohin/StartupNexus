// NOYAU du testeur (v1.3) : ce que tous les blocs partagent — l'app à juger (sa description, sa
// matrice, son schéma), les personnes d'essai, les tentatives jugées sur l'état de la BASE, et le
// rapport. Il ne contient AUCUNE vérification : elles sont dans verification/blocs/, une par bloc.
import { ORMError, ZenStackClient } from '@zenstackhq/orm';
import { PostgresDialect } from '@zenstackhq/orm/dialects/postgres';
import { PolicyPlugin } from '@zenstackhq/plugin-policy';
import { readFileSync, writeFileSync } from 'node:fs';
import { Pool } from 'pg';
import { construireCas } from './cas.mts';

// ─── Ce que chaque cas fournit (adaptateur) ────────────────────────────────
export type User = { id: string; role: string };
export type Users = Record<string, User[]>; // rôle → [utilisateur 1, 2, 3 (neuf, sans profil)]
export type World = Record<string, string>; // identifiants nommés créés par le seed
export type EntitySpec = {
    model: string; // nom côté client (lowerCamel)
    ownerField?: string; // champ qui porte l'identifiant du propriétaire (profil, collection)
    profile?: boolean; // fiche unique par utilisateur
    stateField?: string;
    editField?: string; // un champ texte que « modifier » change (v1.1 : absent si la fiche n'en a pas)
    // Rôles qui créent des fiches À LEUR NOM sans être le rôle propriétaire (« pour son compte ») :
    // la matrice D1 ne sait pas le dire (un seul rôle propriétaire) — trou de vocabulaire noté.
    createsForSelf?: string[];
    build: (w: World, owner: User | null) => Record<string, unknown>; // données valides de création
};
export type Case = {
    matrix: string;
    roles: string[];
    entities: Record<string, EntitySpec>;
    resetOrder: string[]; // modèles à vider, enfants d'abord
    seed: (raw: any, users: Users) => Promise<World>;
};
export type Cell = {
    see?: 'none' | 'own' | 'published' | 'all';
    see_via?: string[];
    create?: 'no' | 'yes' | 'auto';
    edit?: boolean;
    edit_while?: string[];
    delete?: boolean;
    delete_while?: string[];
    transitions?: Record<string, string[]>;
};
// Un BLOC du testeur : les vérifications d'un mot de vocabulaire, pour un acteur et une fiche.
export type Bloc = { nom: string; essayer: (acteur: string, fiche: string) => Promise<void> };

// ─── Mise en place ──────────────────────────────────────────────────────────
// v1.1 (changements 1 et 2) : tout vient des fichiers produits par l'usine pour CETTE app.
const lire = (chemin: string) => JSON.parse(readFileSync(new URL(chemin, import.meta.url), 'utf8'));
const description = lire('./description.json');
export const kase: Case = construireCas(description, lire('../depart.json'));
export const { schema } = await import('../zenstack/schema.ts');
const url = process.env.DATABASE_URL!;
const expected: { cells: Record<string, Record<string, Cell>> } = { cells: {} };
for (const c of lire('./matrice.json').cells) (expected.cells[c.actor] ??= {})[c.entity] = c;
const access = description.acces;

export const raw: any = new ZenStackClient(schema, { dialect: new PostgresDialect({ pool: new Pool({ connectionString: url }) }) });
const policy: any = raw.$use(new PolicyPlugin());
export const as = (u: User | null) => (u ? policy.$setAuth(u) : policy);

export const users: Users = Object.fromEntries(
    kase.roles.map((r) => [r, [1, 2, 3].map((i) => ({ id: `${r}_${i}`, role: r }))]),
);
// (E4 — trou de couverture corrigé) l'INTRUS : quelqu'un de connecté mais sans rôle déclaré
// (inscription restée ouverte chez Clerk, par exemple). Moindre privilège : il a exactement les
// droits du visiteur. SANS_INTRUS=1 le retire (pour mesurer un schéma qui ne le gère pas encore).
const INTRUDER: User = { id: 'intrus_1', role: 'intrus' };
const withIntruder = process.env.SANS_INTRUS !== '1';
export const actors = ['visitor', ...(withIntruder ? ['intrus'] : []), ...kase.roles];
export const userOf = (actor: string, i = 0): User | null =>
    actor === 'visitor' ? null : actor === 'intrus' ? INTRUDER : users[actor][i];
export const cellOf = (actor: string, entity: string): Cell =>
    expected.cells?.[actor === 'intrus' ? 'visitor' : actor]?.[entity] ?? {};
export const ownerRole = (entity: string): string | undefined =>
    access.entities.find((e: any) => e.name === entity)?.owner ?? undefined;
export const statesOf = (entity: string): string[] => {
    const p = access.entities.find((e: any) => e.name === entity)?.process;
    if (!p) return [];
    return [...new Set<string>([...Object.keys(p.transitions), ...Object.values<string[]>(p.transitions).flat()])];
};
export const initialOf = (entity: string): string | undefined =>
    access.entities.find((e: any) => e.name === entity)?.process?.initial;

// ─── Résultats ──────────────────────────────────────────────────────────────
export type Outcome = { ok: boolean; reason?: string; message?: string };
const results: { actor: string; entity: string; label: string; want: boolean; got: Outcome }[] = [];

async function attempt(fn: () => Promise<unknown>): Promise<Outcome> {
    try {
        await fn();
        return { ok: true };
    } catch (e) {
        if (e instanceof ORMError && (e.reason === 'rejected-by-policy' || e.reason === 'not-found'))
            return { ok: false, reason: e.reason };
        return { ok: false, reason: 'ERREUR', message: (e as Error).message.split('\n')[0].slice(0, 160) };
    }
}
export function record(actor: string, entity: string, label: string, want: boolean, got: Outcome) {
    results.push({ actor, entity, label, want, got });
}
export const observed = (ok: boolean): Outcome => ({ ok });

// ─── Écritures : jugées sur l'état de la BASE, pas sur la réponse ───────────
// (E4, 7 oct — défaut de conception corrigé : ZenStack 3.9.7 peut répondre « refusé » parce que
// le résultat n'est pas relisible, alors que l'écriture a bien eu lieu.)
function judged(res: Outcome, wrote: boolean): Outcome {
    if (wrote) return res.ok ? { ok: true } : { ok: true, reason: 'ÉCRIT MALGRÉ LE REFUS', message: res.message ?? res.reason };
    return res.ok ? { ok: false, reason: 'RÉPONSE OK SANS ÉCRITURE' } : res;
}
let stamp = 0;
export const freshText = (s: string) => `${s} #${++stamp}`;
export async function tryCreate(u: User | null, entity: string, data: Record<string, unknown>): Promise<Outcome> {
    const m = raw[kase.entities[entity].model];
    const before = new Set((await m.findMany({ select: { id: true } })).map((r: any) => r.id));
    const res = await attempt(() => as(u)[kase.entities[entity].model].create({ data }));
    const created = (await m.findMany({ select: { id: true } })).filter((r: any) => !before.has(r.id));
    for (const r of created) await m.delete({ where: { id: r.id } }); // remise en état
    return judged(res, created.length > 0);
}
export async function tryUpdate(u: User | null, entity: string, id: string, data: Record<string, unknown>): Promise<Outcome> {
    const m = raw[kase.entities[entity].model];
    const before = await m.findUnique({ where: { id } });
    const res = await attempt(() => as(u)[kase.entities[entity].model].update({ where: { id }, data }));
    const after = await m.findUnique({ where: { id } });
    const changed = Object.keys(data).some((k) => JSON.stringify(after?.[k]) !== JSON.stringify(before?.[k]));
    if (changed) await m.update({ where: { id }, data: Object.fromEntries(Object.keys(data).map((k) => [k, before[k]])) });
    return judged(res, changed);
}
export async function tryDelete(u: User | null, entity: string, id: string): Promise<Outcome> {
    const m = raw[kase.entities[entity].model];
    const res = await attempt(() => as(u)[kase.entities[entity].model].delete({ where: { id } }));
    return judged(res, !(await m.findUnique({ where: { id } })));
}

// ─── Relations lues dans le schéma généré ───────────────────────────────────
export const modelDef = (entity: string) => schema.models[entity];
// Clés étrangères simples (champ local → modèle cible), hors lien vers le propriétaire.
export function foreignKeys(entity: string): { fk: string; target: string; ref: string }[] {
    const out = [];
    for (const f of Object.values<any>(modelDef(entity).fields)) {
        const rel = f.relation;
        if (rel?.fields?.length === 1 && kase.entities[f.type]) {
            if (rel.fields[0] === kase.entities[entity].ownerField) continue;
            out.push({ fk: rel.fields[0], target: f.type, ref: rel.references[0] });
        }
    }
    return out;
}
// Valeurs de `entity` (clé référencée) visibles AU TRAVERS des fiches de `via` que l'acteur voit.
export async function idsVisibleVia(actor: string, entity: string, via: string): Promise<Set<string>> {
    const ids = new Set<string>();
    for (const f of Object.values<any>(modelDef(via).fields)) {
        if (f.type !== entity || !f.relation) continue;
        const rows = await as(userOf(actor))[kase.entities[via].model].findMany({ include: { [f.name]: true } });
        for (const r of rows) for (const x of [r[f.name]].flat()) if (x) ids.add(x.id);
    }
    return ids;
}

// ─── Cibles ─────────────────────────────────────────────────────────────────
// La fiche sur laquelle l'acteur agit : la sienne s'il ne voit que les siennes, sinon celle d'un autre.
export async function target(actor: string, entity: string): Promise<any> {
    const spec = kase.entities[entity];
    const m = raw[spec.model];
    const u = userOf(actor);
    if (spec.ownerField && u) {
        const mine = await m.findFirst({ where: { [spec.ownerField]: u.id } });
        if (cellOf(actor, entity).see === 'own' && mine) return mine;
        const other = await m.findFirst({ where: { [spec.ownerField]: { not: u.id } } });
        return other ?? mine;
    }
    return m.findFirst();
}
// Le propriétaire d'une fiche créée par `actor` : lui-même s'il est du rôle propriétaire, sinon
// un utilisateur du rôle propriétaire (saisie pour autrui).
export function ownerFor(actor: string, entity: string): User | null {
    const role = ownerRole(entity);
    if (!role || !kase.entities[entity].ownerField) return null;
    if (actor === role || kase.entities[entity].createsForSelf?.includes(actor)) return userOf(actor);
    return users[role][0];
}
export async function setState(entity: string, id: string, state: string) {
    const spec = kase.entities[entity];
    await raw[spec.model].update({ where: { id }, data: { [spec.stateField!]: state } });
}
// Les fiches de départ créées pour les essais (rempli par lancer, avant les blocs).
export let world: World = {};

// ─── Déroulé : d'abord « voir » pour tous, puis chaque bloc d'action par acteur et par fiche ───
export async function lancer(blocsVoir: Bloc[], blocsAgir: Bloc[]) {
    for (const m of kase.resetOrder) await raw[m].deleteMany();
    world = await kase.seed(raw, users);
    for (const b of blocsVoir) for (const a of actors) for (const e of Object.keys(kase.entities)) await b.essayer(a, e);
    for (const a of actors)
        for (const e of Object.keys(kase.entities))
            for (const b of blocsAgir) await b.essayer(a, e);
    rapport();
}

// ─── Rapport ────────────────────────────────────────────────────────────────
// Un refus dû à une ERREUR (et non à une règle) n'est jamais compté comme conforme.
function rapport() {
    const verdict = (r: (typeof results)[number]) =>
        r.got.reason === 'ERREUR' ? 'erreur' : r.got.ok === r.want ? 'ok' : 'faux';
    const failures = results.filter((r) => verdict(r) !== 'ok');
    console.log(`\n▶ ${kase.matrix} — ${results.length} vérifications dérivées de la matrice`);
    for (const a of actors) {
        for (const e of Object.keys(kase.entities)) {
            const rs = results.filter((r) => r.actor === a && r.entity === e);
            if (!rs.length) continue;
            const bad = rs.filter((r) => verdict(r) !== 'ok').length;
            console.log(`  ${bad ? '❌' : '✅'} ${a.padEnd(14)} ${e.padEnd(20)} ${rs.length - bad}/${rs.length}`);
        }
    }
    if (failures.length) {
        console.log('\n  Écarts :');
        for (const f of failures)
            console.log(`   • ${f.actor} / ${f.entity} / ${f.label} : attendu ${f.want ? 'PERMIS' : 'REFUSÉ'}, obtenu ${
                f.got.ok ? 'PERMIS' : `REFUSÉ (${f.got.reason}${f.got.message ? ' : ' + f.got.message : ''})`}`);
    }
    const errors = results.filter((r) => r.got.reason === 'ERREUR');
    if (errors.length) console.log(`\n  ⚠ ${errors.length} refus dus à une ERREUR (pas à une règle) — à examiner`);
    const silent = results.filter((r) => r.got.reason === 'ÉCRIT MALGRÉ LE REFUS');
    if (silent.length) console.log(`\n  ⚠ ${silent.length} écriture(s) faite(s) en base alors que la réponse disait « refusé »`);
    console.log(`\n  ${results.length - failures.length}/${results.length} conformes à la matrice`);
    // TESTEUR_DETAIL=<fichier> : la liste complète des vérifications (pour comparer deux versions du testeur)
    if (process.env.TESTEUR_DETAIL)
        writeFileSync(process.env.TESTEUR_DETAIL, JSON.stringify(results.map((r) => ({ acteur: r.actor, fiche: r.entity,
            essai: r.label, attendu: r.want, obtenu: r.got.ok, raison: r.got.reason ?? null })), null, 1));
    process.exit(failures.length ? 1 : 0);
}
