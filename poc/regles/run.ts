// ▌ VERSION FIGÉE 1.0 — 7 oct 2026, après l'E4 (test par mutation : etudes/04-testeur-prouve.md).
// ▌ Toute modification ultérieure = nouvelle version, notée avec sa nature (erreur / besoin / rustine).
// Testeur générique : lit la matrice ATTENDUE d'un cas et essaie chaque case contre la base,
// avec le client AVEC règles, rôle par rôle. Aucun test n'est écrit à la main : ils sont dérivés
// de la matrice (premier morceau des « tests par rôle générés » du niveau 1).
// Usage : npx tsx run.ts notes-frais
import { ORMError, ZenStackClient } from '@zenstackhq/orm';
import { PostgresDialect } from '@zenstackhq/orm/dialects/postgres';
import { PolicyPlugin } from '@zenstackhq/plugin-policy';
import { readFileSync } from 'node:fs';
import { Pool } from 'pg';
import { parse } from 'yaml';

// ─── Ce que chaque cas fournit (adaptateur) ────────────────────────────────
export type User = { id: string; role: string };
export type Users = Record<string, User[]>; // rôle → [utilisateur 1, 2, 3 (neuf, sans profil)]
export type World = Record<string, string>; // identifiants nommés créés par le seed
export type EntitySpec = {
    model: string; // nom côté client (lowerCamel)
    ownerField?: string; // champ qui porte l'identifiant du propriétaire (profil, collection)
    profile?: boolean; // fiche unique par utilisateur
    stateField?: string;
    editField: string; // un champ texte que « modifier » change
    // Rôles qui créent des fiches À LEUR NOM sans être le rôle propriétaire (« pour son compte ») :
    // la matrice D1 ne sait pas le dire (un seul rôle propriétaire) — trou de vocabulaire noté.
    createsForSelf?: string[];
    build: (w: World, owner: User | null) => Record<string, unknown>; // données valides de création
};
export type Case = {
    matrix: string; // harness/matrices/<matrix>.{access,expected}.yaml
    roles: string[];
    entities: Record<string, EntitySpec>;
    resetOrder: string[]; // modèles à vider, enfants d'abord
    seed: (raw: any, users: Users) => Promise<World>;
};

type Cell = {
    see?: 'none' | 'own' | 'published' | 'all';
    see_via?: string[];
    create?: 'no' | 'yes' | 'auto';
    edit?: boolean;
    edit_while?: string[];
    delete?: boolean;
    delete_while?: string[];
    transitions?: Record<string, string[]>;
};

// ─── Mise en place ──────────────────────────────────────────────────────────
const caseName = process.argv[2];
if (!caseName) throw new Error('usage : npx tsx run.ts <cas>');
const kase: Case = (await import(`./cases/${caseName}/case.ts`)).default;
const { schema } = await import(`./cases/${caseName}/gen/schema.ts`);
const url = readFileSync(`cases/${caseName}/gen/database-url.txt`, 'utf8').trim();
const MATRICES = '../../factory-sprint0/harness/matrices';
const expected = parse(readFileSync(`${MATRICES}/${kase.matrix}.expected.yaml`, 'utf8'));
const access = parse(readFileSync(`${MATRICES}/${kase.matrix}.access.yaml`, 'utf8'));

const raw: any = new ZenStackClient(schema, { dialect: new PostgresDialect({ pool: new Pool({ connectionString: url }) }) });
const policy: any = raw.$use(new PolicyPlugin());
const as = (u: User | null) => (u ? policy.$setAuth(u) : policy);

const users: Users = Object.fromEntries(
    kase.roles.map((r) => [r, [1, 2, 3].map((i) => ({ id: `${r}_${i}`, role: r }))]),
);
// (E4 — trou de couverture corrigé) l'INTRUS : quelqu'un de connecté mais sans rôle déclaré
// (inscription restée ouverte chez Clerk, par exemple). Moindre privilège : il a exactement les
// droits du visiteur. SANS_INTRUS=1 le retire (pour mesurer un schéma qui ne le gère pas encore).
const INTRUDER: User = { id: 'intrus_1', role: 'intrus' };
const withIntruder = process.env.SANS_INTRUS !== '1';
const actors = ['visitor', ...(withIntruder ? ['intrus'] : []), ...kase.roles];
const userOf = (actor: string, i = 0): User | null =>
    actor === 'visitor' ? null : actor === 'intrus' ? INTRUDER : users[actor][i];
const cellOf = (actor: string, entity: string): Cell =>
    expected.cells?.[actor === 'intrus' ? 'visitor' : actor]?.[entity] ?? {};
const ownerRole = (entity: string): string | undefined =>
    access.entities.find((e: any) => e.name === entity)?.owner ?? undefined;
const statesOf = (entity: string): string[] => {
    const p = access.entities.find((e: any) => e.name === entity)?.process;
    if (!p) return [];
    return [...new Set<string>([...Object.keys(p.transitions), ...Object.values<string[]>(p.transitions).flat()])];
};
const initialOf = (entity: string): string | undefined =>
    access.entities.find((e: any) => e.name === entity)?.process?.initial;

// ─── Résultats ──────────────────────────────────────────────────────────────
type Outcome = { ok: boolean; reason?: string; message?: string };
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
function record(actor: string, entity: string, label: string, want: boolean, got: Outcome) {
    results.push({ actor, entity, label, want, got });
}
const observed = (ok: boolean): Outcome => ({ ok });

// ─── Écritures : jugées sur l'état de la BASE, pas sur la réponse ───────────
// (E4, 7 oct — défaut de conception corrigé : ZenStack 3.9.7 peut répondre « refusé » parce que
// le résultat n'est pas relisible, alors que l'écriture a bien eu lieu.)
function judged(res: Outcome, wrote: boolean): Outcome {
    if (wrote) return res.ok ? { ok: true } : { ok: true, reason: 'ÉCRIT MALGRÉ LE REFUS', message: res.message ?? res.reason };
    return res.ok ? { ok: false, reason: 'RÉPONSE OK SANS ÉCRITURE' } : res;
}
let stamp = 0;
const freshText = (s: string) => `${s} #${++stamp}`;
async function tryCreate(u: User | null, entity: string, data: Record<string, unknown>): Promise<Outcome> {
    const m = raw[kase.entities[entity].model];
    const before = new Set((await m.findMany({ select: { id: true } })).map((r: any) => r.id));
    const res = await attempt(() => as(u)[kase.entities[entity].model].create({ data }));
    const created = (await m.findMany({ select: { id: true } })).filter((r: any) => !before.has(r.id));
    for (const r of created) await m.delete({ where: { id: r.id } }); // remise en état
    return judged(res, created.length > 0);
}
async function tryUpdate(u: User | null, entity: string, id: string, data: Record<string, unknown>): Promise<Outcome> {
    const m = raw[kase.entities[entity].model];
    const before = await m.findUnique({ where: { id } });
    const res = await attempt(() => as(u)[kase.entities[entity].model].update({ where: { id }, data }));
    const after = await m.findUnique({ where: { id } });
    const changed = Object.keys(data).some((k) => JSON.stringify(after?.[k]) !== JSON.stringify(before?.[k]));
    if (changed) await m.update({ where: { id }, data: Object.fromEntries(Object.keys(data).map((k) => [k, before[k]])) });
    return judged(res, changed);
}
async function tryDelete(u: User | null, entity: string, id: string): Promise<Outcome> {
    const m = raw[kase.entities[entity].model];
    const res = await attempt(() => as(u)[kase.entities[entity].model].delete({ where: { id } }));
    return judged(res, !(await m.findUnique({ where: { id } })));
}

// ─── Relations lues dans le schéma généré ───────────────────────────────────
const modelDef = (entity: string) => schema.models[entity];
// Clés étrangères simples (champ local → modèle cible), hors lien vers le propriétaire.
function foreignKeys(entity: string): { fk: string; target: string; ref: string }[] {
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
// Les autres champs d'une fiche (ni identifiant, ni état), avec une AUTRE valeur valide :
// une étape du circuit ne doit en changer aucun (E4 — trou de couverture corrigé : seul le champ
// « modifiable » était essayé, et seulement sur la première flèche).
async function otherFieldValues(entity: string, row: any): Promise<[string, unknown][]> {
    const spec = kase.entities[entity];
    const out: [string, unknown][] = [];
    for (const f of Object.values<any>(modelDef(entity).fields)) {
        if (f.id || f.relation || f.name === spec.stateField) continue;
        if (f.foreignKeyFor || f.name === spec.ownerField) {
            const rel = Object.values<any>(modelDef(entity).fields).find((g) => g.relation?.fields?.[0] === f.name);
            const targetModel = rel && kase.entities[rel.type]?.model;
            if (!targetModel) continue;
            const ref = rel.relation.references[0];
            const other = (await raw[targetModel].findMany()).find((r: any) => r[ref] !== row[f.name]);
            if (other) out.push([f.name, other[ref]]);
        } else if (f.type === 'String') out.push([f.name, freshText('autre valeur')]);
        else if (f.type === 'Int') out.push([f.name, (row[f.name] ?? 0) + 1]);
        else if (f.type === 'Boolean') out.push([f.name, !row[f.name]]);
    }
    return out;
}
// Valeurs de `entity` (clé référencée) visibles AU TRAVERS des fiches de `via` que l'acteur voit.
async function idsVisibleVia(actor: string, entity: string, via: string): Promise<Set<string>> {
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
async function target(actor: string, entity: string): Promise<any> {
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
function ownerFor(actor: string, entity: string): User | null {
    const role = ownerRole(entity);
    if (!role || !kase.entities[entity].ownerField) return null;
    if (actor === role || kase.entities[entity].createsForSelf?.includes(actor)) return userOf(actor);
    return users[role][0];
}

// ─── Les vérifications, toutes dérivées de la matrice ───────────────────────
async function checkSee(actor: string, entity: string) {
    const spec = kase.entities[entity];
    const c = cellOf(actor, entity);
    const u = userOf(actor);
    const rows: any[] = await as(u)[spec.model].findMany();
    const total = await raw[spec.model].count();
    const see = c.see ?? 'none';
    if (see === 'all') {
        record(actor, entity, `voir : toutes (${rows.length}/${total})`, true, observed(rows.length === total && total > 0));
    } else if (see === 'own') {
        const mine = await raw[spec.model].count({ where: { [spec.ownerField!]: u!.id } });
        const onlyMine = rows.every((r) => r[spec.ownerField!] === u!.id);
        record(actor, entity, `voir : les siennes seulement (${rows.length}, attendu ${mine})`, true,
            observed(onlyMine && rows.length === mine && mine > 0));
    } else if (c.see_via?.length) {
        const allowed = new Set<string>();
        for (const v of c.see_via) for (const id of await idsVisibleVia(actor, entity, v)) allowed.add(id);
        const ok = rows.every((r) => allowed.has(r.id)) && rows.length === allowed.size && allowed.size > 0;
        record(actor, entity, `voir : seulement au travers de ${c.see_via.join(', ')} (${rows.length}, attendu ${allowed.size})`,
            true, observed(ok));
        // et l'acteur ne voit pas la fiche d'un élément qui n'est référencé par rien de visible
        const hidden = await raw[spec.model].findMany({ where: { id: { notIn: [...allowed] } } });
        if (hidden.length)
            record(actor, entity, `voir : pas une fiche non reliée, même par identifiant`, false,
                observed(!!(await as(u)[spec.model].findUnique({ where: { id: hidden[0].id } }))));
    } else {
        record(actor, entity, `voir : rien (${rows.length})`, true, observed(rows.length === 0));
    }
    // accès forcé : la fiche d'un autre, demandée par son identifiant
    if (see === 'own' && u) {
        const other = await raw[spec.model].findFirst({ where: { [spec.ownerField!]: { not: u.id } } });
        if (other)
            record(actor, entity, `voir : pas la fiche d'un autre, même par identifiant`, false,
                observed(!!(await as(u)[spec.model].findUnique({ where: { id: other.id } }))));
    }
}

async function checkCreate(actor: string, entity: string) {
    const spec = kase.entities[entity];
    const c = cellOf(actor, entity);
    const u = userOf(actor);
    const create = c.create ?? 'no';
    if (spec.profile) {
        const role = ownerRole(entity)!;
        const fresh = users[role][2];
        if (actor !== 'visitor' && actor !== role)
            record(actor, entity, `créer : un profil (pas son rôle)`, false,
                await tryCreate(u, entity, spec.build({}, { id: u!.id, role: actor })));
        if (actor === role) {
            record(actor, entity, `créer : le profil de quelqu'un d'autre`, false,
                await tryCreate(u, entity, spec.build({}, fresh)));
            record(actor, entity, `créer : son propre profil (première connexion)`, create === 'auto' || create === 'yes',
                await tryCreate(fresh, entity, spec.build({}, fresh)));
        }
        if (actor === 'visitor')
            record(actor, entity, `créer : un profil sans compte`, false,
                await tryCreate(null, entity, spec.build({}, fresh)));
        return;
    }
    const owner = ownerFor(actor, entity) ?? (u && spec.ownerField ? u : null);
    const data = spec.build(world, owner);
    record(actor, entity, `créer`, create === 'yes', await tryCreate(u, entity, data));
    if (create !== 'yes') {
        // (E4 — trou de couverture corrigé) celui qui n'a pas le droit de créer ne le peut pas
        // non plus À SON PROPRE NOM
        if (spec.ownerField && u && owner?.id !== u.id)
            record(actor, entity, `créer : à son propre nom`, false,
                await tryCreate(u, entity, spec.build(world, u)));
        return;
    }
    // pour quelqu'un d'autre de son propre rôle (quand il crée les siennes) — (E4, défaut de mon
    // test corrigé) seul le propriétaire change : les fiches pointées restent les SIENNES, sinon la
    // règle de clôture bloque avant la règle de propriétaire et la masque
    if (spec.ownerField && (actor === ownerRole(entity) || spec.createsForSelf?.includes(actor)))
        record(actor, entity, `créer : au nom d'un autre ${actor}`, false,
            await tryCreate(u, entity, { ...data, [spec.ownerField]: users[actor][1].id }));
    // directement dans un état avancé
    const init = initialOf(entity);
    for (const s of statesOf(entity).filter((s) => s !== init).slice(0, 1))
        record(actor, entity, `créer : directement « ${s} »`, false,
            await tryCreate(u, entity, { ...data, [spec.stateField!]: s }));
    // en pointant une fiche qu'il ne voit pas (règle de clôture : on ne choisit que ce qu'on voit)
    for (const { fk, target: t, ref } of foreignKeys(entity)) {
        const visible = new Set((await as(u)[kase.entities[t].model].findMany()).map((r: any) => r[ref]));
        const hidden = (await raw[kase.entities[t].model].findMany()).find((r: any) => !visible.has(r[ref]));
        if (hidden)
            record(actor, entity, `créer : en pointant ${t} qu'il ne voit pas`, false,
                await tryCreate(u, entity, { ...data, [fk]: hidden[ref] }));
        // cohérence : si la fiche pointée appartient au même rôle propriétaire, ce doit être le MÊME
        // propriétaire (la réparation du client A ne porte pas sur le véhicule du client B)
        const tOwner = kase.entities[t].ownerField;
        if (spec.ownerField && tOwner && owner?.role === ownerRole(t) && data[spec.ownerField]) {
            const foreign = (await raw[kase.entities[t].model].findMany()).find(
                (r: any) => r[tOwner] !== data[spec.ownerField!] && visible.has(r[ref]));
            if (foreign)
                record(actor, entity, `créer : en pointant ${t} d'un AUTRE propriétaire`, false,
                    await tryCreate(u, entity, { ...data, [fk]: foreign[ref] }));
        }
    }
}

async function setState(entity: string, id: string, state: string) {
    const spec = kase.entities[entity];
    await raw[spec.model].update({ where: { id }, data: { [spec.stateField!]: state } });
}

async function checkEdit(actor: string, entity: string) {
    const spec = kase.entities[entity];
    const c = cellOf(actor, entity);
    const u = userOf(actor);
    const t = await target(actor, entity);
    if (!t) return;
    const states = statesOf(entity);
    const edit = (s?: string) =>
        !!c.edit && (!s || !c.edit_while?.length || c.edit_while.includes(s));
    const tryEdit = () => tryUpdate(u, entity, t.id, { [spec.editField]: freshText(`modifié par ${actor}`) });
    if (states.length && spec.stateField) {
        for (const s of states) {
            await setState(entity, t.id, s);
            record(actor, entity, `modifier en « ${s} »`, edit(s), await tryEdit());
        }
        await setState(entity, t.id, t[spec.stateField]);
    } else {
        record(actor, entity, `modifier`, edit(), await tryEdit());
    }
    // modifier la fiche d'un autre quand on ne voit que les siennes
    if (c.see === 'own' && spec.ownerField && u) {
        const other = await raw[spec.model].findFirst({ where: { [spec.ownerField]: { not: u.id } } });
        if (other)
            record(actor, entity, `modifier : la fiche d'un autre`, false,
                await tryUpdate(u, entity, other.id, { [spec.editField]: freshText('pirate') }));
    }
    // (E4 — trou de couverture corrigé) changement de rôle : une fiche restée à son nom d'avant
    // (employé promu responsable) ne se modifie que si son rôle ACTUEL le permet
    if (spec.ownerField && !spec.profile && u && actor !== 'intrus' && actor !== ownerRole(entity) && !kase.entities[entity].createsForSelf?.includes(actor)) {
        const former = { id: u.id, role: ownerRole(entity)! };
        // si le propriétaire doit avoir un profil (lien vers profil.userId), il garde son ancien profil
        const ownerLink = Object.values<any>(modelDef(entity).fields).find((g) => g.relation?.fields?.[0] === spec.ownerField);
        const profileEntity = ownerLink && kase.entities[ownerLink.type]?.profile ? ownerLink.type : undefined;
        const oldProfile = profileEntity
            ? await raw[kase.entities[profileEntity].model].create({ data: kase.entities[profileEntity].build(world, former) })
            : undefined;
        const inherited = await raw[spec.model].create({ data: spec.build(world, former) });
        record(actor, entity, `modifier : sa fiche d'avant un changement de rôle`, edit(inherited[spec.stateField ?? ''] ?? undefined),
            await tryUpdate(u, entity, inherited.id, { [spec.editField]: freshText('ancien rôle') }));
        await raw[spec.model].delete({ where: { id: inherited.id } });
        if (oldProfile) await raw[kase.entities[profileEntity!].model].delete({ where: { id: oldProfile.id } });
    }
    // changer de propriétaire (vers un autre propriétaire qui existe vraiment)
    // (un profil est unique par utilisateur : on vise un utilisateur sans profil)
    const otherOwner = !spec.ownerField
        ? undefined
        : spec.profile
          ? 'utilisateur_sans_profil'
          : (await raw[spec.model].findFirst({ where: { [spec.ownerField]: { not: t[spec.ownerField] } } }))?.[spec.ownerField];
    if (spec.ownerField && otherOwner && edit(states[0]) && u) {
        if (states.length) await setState(entity, t.id, (c.edit_while ?? [])[0] ?? states[0]);
        record(actor, entity, `modifier : changer le propriétaire`, false,
            await tryUpdate(u, entity, t.id, { [spec.ownerField!]: otherOwner }));
        if (states.length) await setState(entity, t.id, t[spec.stateField!]);
    }
}

async function checkTransitions(actor: string, entity: string) {
    const spec = kase.entities[entity];
    const states = statesOf(entity);
    if (!states.length || !spec.stateField) return;
    const c = cellOf(actor, entity);
    const u = userOf(actor);
    const t = await target(actor, entity);
    if (!t) return;
    for (const from of states)
        for (const to of states) {
            if (from === to) continue;
            await setState(entity, t.id, from);
            const want = !!c.transitions?.[from]?.includes(to);
            record(actor, entity, `état « ${from} » → « ${to} »`, want,
                await tryUpdate(u, entity, t.id, { [spec.stateField!]: to }));
        }
    // Une étape ne modifie que l'état : pour CHAQUE flèche permise et CHAQUE autre champ
    // (propriétaire et liens compris), l'étape qui change aussi ce champ est refusée.
    for (const [from, tos] of Object.entries(c.transitions ?? {}))
        for (const to of tos) {
            await setState(entity, t.id, from);
            const row = await raw[spec.model].findUnique({ where: { id: t.id } });
            for (const [field, value] of await otherFieldValues(entity, row))
                record(actor, entity, `étape « ${from} » → « ${to} » en changeant aussi ${field}`, false,
                    await tryUpdate(u, entity, t.id, { [spec.stateField!]: to, [field]: value }));
        }
    await setState(entity, t.id, t[spec.stateField]);
}

async function checkDelete(actor: string, entity: string) {
    const spec = kase.entities[entity];
    if (spec.profile) return; // un profil ne se supprime pas en D1
    const c = cellOf(actor, entity);
    const u = userOf(actor);
    const t = await target(actor, entity);
    if (!t) return;
    const owner = spec.ownerField ? { id: t[spec.ownerField], role: ownerRole(entity)! } : null;
    const disposable = await raw[spec.model].create({ data: spec.build(world, owner) });
    const got = await tryDelete(u, entity, disposable.id);
    record(actor, entity, `supprimer`, !!c.delete, got);
    if (!got.ok) await raw[spec.model].delete({ where: { id: disposable.id } });
}

// ─── Déroulé ────────────────────────────────────────────────────────────────
for (const m of kase.resetOrder) await raw[m].deleteMany();
const world = await kase.seed(raw, users);

for (const a of actors) for (const e of Object.keys(kase.entities)) await checkSee(a, e);
for (const a of actors)
    for (const e of Object.keys(kase.entities)) {
        await checkCreate(a, e);
        await checkEdit(a, e);
        await checkTransitions(a, e);
        await checkDelete(a, e);
    }

// ─── Rapport ────────────────────────────────────────────────────────────────
// Un refus dû à une ERREUR (et non à une règle) n'est jamais compté comme conforme.
const verdict = (r: (typeof results)[number]) =>
    r.got.reason === 'ERREUR' ? 'erreur' : r.got.ok === r.want ? 'ok' : 'faux';
const failures = results.filter((r) => verdict(r) !== 'ok');
console.log(`\n▶ ${caseName} — ${results.length} vérifications dérivées de la matrice`);
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
process.exit(failures.length ? 1 : 0);
