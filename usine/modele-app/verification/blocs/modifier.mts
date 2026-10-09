// BLOC « modifier » — la partie JUGER de la modification : selon l'état, jamais la date de
// création, jamais la fiche d'un autre quand on ne voit que les siennes, l'ancienne fiche après un
// changement de rôle, et jamais le propriétaire.
import {
    cellOf, freshText, kase, modelDef, ownerRole, raw, record, setState, statesOf, target, tryUpdate, userOf, world,
    type Bloc,
} from '../noyau.mts';

export const modifier: Bloc = {
    nom: 'modifier',
    async essayer(actor, entity) {
        const spec = kase.entities[entity];
        if (!spec.editField) return; // v1.1 (changement 3) : rien à « modifier » sur une fiche sans champ texte
        const c = cellOf(actor, entity);
        const u = userOf(actor);
        const t = await target(actor, entity);
        if (!t) return;
        const states = statesOf(entity);
        const edit = (s?: string) =>
            !!c.edit && (!s || !c.edit_while?.length || c.edit_while.includes(s));
        const tryEdit = () => tryUpdate(u, entity, t.id, { [spec.editField!]: freshText(`modifié par ${actor}`) });
        if (states.length && spec.stateField) {
            for (const s of states) {
                await setState(entity, t.id, s);
                record(actor, entity, `modifier en « ${s} »`, edit(s), await tryEdit());
            }
            await setState(entity, t.id, t[spec.stateField]);
        } else {
            record(actor, entity, `modifier`, edit(), await tryEdit());
        }
        // v1.2 (changement 6) : même qui peut modifier la fiche ne change pas sa date de création
        if (modelDef(entity).fields.createdAt) {
            const s = states.length && spec.stateField ? states.find((x) => edit(x)) : undefined;
            if (s !== undefined || (!states.length && edit())) {
                if (s !== undefined) await setState(entity, t.id, s);
                record(actor, entity, `modifier : sa date de création`, false,
                    await tryUpdate(u, entity, t.id, { createdAt: new Date(Date.UTC(2020, 0, 1)) }));
                if (s !== undefined) await setState(entity, t.id, t[spec.stateField!]);
            }
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
    },
};
