// BLOC « voir » — la partie JUGER des portées de lecture : rien, les siennes, toutes, au travers
// d'une autre fiche ; et l'accès forcé (une fiche demandée par son identifiant).
import { as, cellOf, idsVisibleVia, kase, observed, raw, record, userOf, type Bloc } from '../noyau.mts';

export const voir: Bloc = {
    nom: 'voir',
    async essayer(actor, entity) {
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
    },
};
