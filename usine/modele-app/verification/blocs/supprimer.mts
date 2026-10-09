// BLOC « supprimer » — la partie JUGER de la suppression : jamais par défaut, seulement si la
// matrice l'accorde (un profil ne se supprime pas).
import { cellOf, kase, ownerRole, raw, record, target, tryDelete, userOf, world, type Bloc } from '../noyau.mts';

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
        const disposable = await raw[spec.model].create({ data: spec.build(world, owner) });
        const got = await tryDelete(u, entity, disposable.id);
        record(actor, entity, `supprimer`, !!c.delete, got);
        if (!got.ok) await raw[spec.model].delete({ where: { id: disposable.id } });
    },
};
