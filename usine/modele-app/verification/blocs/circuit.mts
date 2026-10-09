// BLOC « circuit d'états » — la partie JUGER des étapes : chaque flèche permise ou refusée selon la
// matrice, et une étape qui change AUSSI un autre champ est refusée — champs facultatifs vides,
// puis remplis (v1.2).
import { cellOf, kase, raw, record, setState, statesOf, target, tryUpdate, userOf, type Bloc } from '../noyau.mts';
import { facultatifs, otherFieldValues, remplirFacultatifs } from './champs.mts';

export const circuit: Bloc = {
    nom: 'circuit',
    async essayer(actor, entity) {
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
        // v1.2 (changement 5) : d'abord champs facultatifs vides (données), puis remplis.
        for (const remplis of [false, true]) {
            if (remplis && !(await remplirFacultatifs(entity, t.id))) break;
            const quand = remplis ? ' (champs facultatifs remplis)' : '';
            for (const [from, tos] of Object.entries(c.transitions ?? {}))
                for (const to of tos) {
                    if (remplis) {
                        await setState(entity, t.id, from);
                        record(actor, entity, `état « ${from} » → « ${to} »${quand}`, true,
                            await tryUpdate(u, entity, t.id, { [spec.stateField!]: to }));
                    }
                    await setState(entity, t.id, from);
                    const row = await raw[spec.model].findUnique({ where: { id: t.id } });
                    for (const [field, value] of await otherFieldValues(entity, row))
                        record(actor, entity, `étape « ${from} » → « ${to} » en changeant aussi ${field}${value === null ? ' (vidé)' : ''}${quand}`,
                            false, await tryUpdate(u, entity, t.id, { [spec.stateField!]: to, [field]: value }));
                }
        }
        if (facultatifs(entity).length)   // la fiche retrouve ses valeurs d'avant
            await raw[spec.model].update({ where: { id: t.id }, data: Object.fromEntries(facultatifs(entity).map((f) => [f.name, t[f.name]])) });
        await setState(entity, t.id, t[spec.stateField]);
    },
};
