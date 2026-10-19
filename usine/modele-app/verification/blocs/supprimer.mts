// BLOC « supprimer » — la partie JUGER de la suppression : jamais par défaut, seulement si la
// matrice l'accorde, et seulement DANS LES ÉTATS qu'elle permet (un profil ne se supprime pas).
import {
    cellOf, foreignKeys, kase, ownerRole, raw, record, setState, statesOf, target, tryDelete, userOf, users, world, type Bloc,
} from '../noyau.mts';

export const supprimer: Bloc = {
    nom: 'supprimer',
    async essayer(actor, entity) {
        const spec = kase.entities[entity];
        if (spec.profile) return; // un profil ne se supprime pas en D1
        const c = cellOf(actor, entity);
        const u = userOf(actor);
        const t = await target(actor, entity);
        if (!t) return;
        const owner = spec.ownerField ? { id: t[spec.ownerField], role: ownerRole(entity)! } : null;
        // v1.4 (changement 9, trou du juge) : la suppression permise seulement dans certains états
        // (delete_while) n'était pas essayée état par état
        const states = statesOf(entity);
        const permis = (s?: string) => !!c.delete && (s === undefined || !c.delete_while?.length || c.delete_while.includes(s));
        for (const s of states.length && spec.stateField ? states : [undefined]) {
            const disposable = await raw[spec.model].create({ data: spec.build(world, owner) });
            if (s !== undefined) await setState(entity, disposable.id, s);
            const got = await tryDelete(u, entity, disposable.id);
            record(actor, entity, s === undefined ? `supprimer` : `supprimer en « ${s} »`, permis(s), got);
            if (!got.ok) await raw[spec.model].delete({ where: { id: disposable.id } });
        }
        // v1.4 (changement 10) : INTÉGRITÉ — même qui a le droit de supprimer ne supprime pas une fiche que
        // d'autres fiches désignent (jamais de suppression en cascade ; trouvé par les tests d'écran)
        const avecEtats = !!(states.length && spec.stateField);
        const etatPermis = avecEtats ? states.find((s) => permis(s)) : undefined;
        if (avecEtats ? etatPermis === undefined : !permis()) return;
        for (const [nomR, specR] of Object.entries(kase.entities)) {
            const fkR = foreignKeys(nomR).find((x) => x.target === entity);
            if (!fkR) continue;
            const visee = await raw[spec.model].create({ data: spec.build(world, owner) });
            if (etatPermis !== undefined) await setState(entity, visee.id, etatPermis);
            const proprioR = specR.ownerField ? users[ownerRole(nomR)!][0] : null;
            const designante = await raw[specR.model].create({ data: { ...specR.build(world, proprioR), [fkR.fk]: visee[fkR.ref] } });
            record(actor, entity, `supprimer : une fiche désignée par ${nomR}`, false, await tryDelete(u, entity, visee.id));
            await raw[specR.model].delete({ where: { id: designante.id } });
            if (await raw[spec.model].findUnique({ where: { id: visee.id } })) await raw[spec.model].delete({ where: { id: visee.id } });
            break;
        }
    },
};
