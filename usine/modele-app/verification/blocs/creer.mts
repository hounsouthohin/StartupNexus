// BLOC « créer » — la partie JUGER de la création : profil (première connexion, pas celui d'un
// autre), créer ou non, à son nom ou au nom d'un autre, jamais dans un état avancé, ne pointer que
// ce qu'on voit (clôture), le même propriétaire que la fiche pointée (cohérence).
import {
    as, cellOf, foreignKeys, initialOf, kase, ownerFor, ownerRole, raw, record, statesOf, tryCreate, userOf, users, world,
    type Bloc,
} from '../noyau.mts';

export const creer: Bloc = {
    nom: 'créer',
    async essayer(actor, entity) {
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
    },
};
