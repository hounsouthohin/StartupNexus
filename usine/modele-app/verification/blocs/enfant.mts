// BLOC « enfant » (N1.3) — la partie JUGER des LIGNES d'une fiche (fiches enfants), doctrine du 10 oct :
//   1. voir : exactement les lignes des parents qu'on voit (aucune d'un parent caché) ;
//   2. gérer (ajouter, modifier, retirer) : seulement qui peut modifier le parent, et seulement dans les
//      états où le parent est modifiable — essayé état par état du parent ; jamais sur le parent d'un autre
//      quand on ne voit que les siens ;
//   2c. sa date de création ne change pas ; ses autres liens se re-désignent vers une fiche visible, jamais cachée ;
//   3. une ligne ne change jamais de parent ;
//   4. supprimer le parent supprime ses lignes (la seule cascade de l'usine).
// Les attentes viennent de la matrice (la case de la LIGNE : create, edit, delete et leurs états, qui sont
// ceux du parent) ; tout est jugé sur l'état de la base.
import {
    as, cellOf, foreignKeys, freshText, kase, observed, ownerFor, ownerRole, raw, record, setState, statesOf, tryCreate,
    tryDelete, tryUpdate, userOf, users, world, type Bloc,
} from '../noyau.mts';

const dans = (etats: string[] | undefined, s?: string) => s === undefined || !etats?.length || etats.includes(s);

export const enfant: Bloc = {
    nom: 'enfant',
    enfants: true,
    async essayer(actor, entity) {
        const spec = kase.entities[entity];
        const P = spec.parent!;
        const ps = kase.entities[P];
        const fk = `${ps.model}Id`;
        const c = cellOf(actor, entity);
        const u = userOf(actor);
        const ligne = (parentId: string) => ({ ...spec.build(world, null), [fk]: parentId });

        // 1. voir : les lignes des parents qu'il voit, et seulement elles
        const parentsVus = new Set((await as(u)[ps.model].findMany({ select: { id: true } })).map((r: any) => r.id));
        const toutes: any[] = await raw[spec.model].findMany();
        const voit = !!c.see && c.see !== 'none';
        const attendues = voit ? toutes.filter((l) => parentsVus.has(l[fk])) : [];
        const vues: any[] = await as(u)[spec.model].findMany();
        record(actor, entity, `voir : les lignes des ${P} qu'il voit (${attendues.length}/${toutes.length})`, true,
            observed(vues.length === attendues.length && vues.every((l) => attendues.some((a) => a.id === l.id))));
        if (actor === 'visitor' || actor === 'intrus') {
            // 4. (une fois par sorte de ligne) la base : supprimer le parent supprime ses lignes
            if (actor === 'visitor') {
                const proprio = ps.ownerField ? users[ownerRole(P)!][0] : null;
                if (!ps.profile) {
                    const p = await raw[ps.model].create({ data: ps.build(world, proprio) });
                    const l = await raw[spec.model].create({ data: ligne(p.id) });
                    await raw[ps.model].delete({ where: { id: p.id } });
                    record(actor, entity, `base : supprimer un(e) ${P} supprime ses lignes`, true,
                        observed(!(await raw[spec.model].findUnique({ where: { id: l.id } }))));
                }
            }
        }

        // 2. gérer, état par état du PARENT, sur un parent qu'il peut toucher (le sien s'il ne voit que les siens)
        const etats = ps.stateField ? statesOf(P) : [];
        const proprio = ps.ownerField ? (ps.profile ? u : ownerFor(actor, P)) : null;
        for (const s of etats.length ? etats : [undefined]) {
            let parentId: string;
            let jetable = false;
            if (ps.profile) {
                if (!u || !world[`${P}:${u.id}`]) break;     // sans profil à lui, rien à gérer
                parentId = world[`${P}:${u.id}`];
            } else {
                parentId = (await raw[ps.model].create({ data: ps.build(world, proprio) })).id;
                jetable = true;
                if (s !== undefined) await setState(P, parentId, s);
            }
            const ou = s === undefined ? '' : ` (parent en « ${s} »)`;
            record(actor, entity, `ajouter une ligne${ou}`, c.create === 'yes' && dans(c.create_while, s),
                await tryCreate(u, entity, ligne(parentId)));
            const l = await raw[spec.model].create({ data: ligne(parentId) });
            if (spec.editField)
                record(actor, entity, `modifier une ligne${ou}`, !!c.edit && dans(c.edit_while, s),
                    await tryUpdate(u, entity, l.id, { [spec.editField]: freshText('Modifié') }));
            record(actor, entity, `retirer une ligne${ou}`, !!c.delete && dans(c.delete_while, s), await tryDelete(u, entity, l.id));
            if (jetable) await raw[ps.model].delete({ where: { id: parentId } });   // ses lignes partent avec lui
            else await raw[spec.model].deleteMany({ where: { id: l.id } });
        }

        // 2b. le parent d'un AUTRE, quand il ne voit que les siens : jamais
        if (u && ps.ownerField && !ps.profile && cellOf(actor, P).see === 'own' && ownerRole(P) === actor) {
            const autre = users[actor].find((x) => x.id !== u.id)!;
            const p = await raw[ps.model].create({ data: ps.build(world, autre) });
            const etatPermis = etats.find((s) => dans(c.edit_while, s));
            if (etatPermis) await setState(P, p.id, etatPermis);
            record(actor, entity, `ajouter une ligne au ${P} d'un autre`, false, await tryCreate(u, entity, ligne(p.id)));
            const l = await raw[spec.model].create({ data: ligne(p.id) });
            if (spec.editField)
                record(actor, entity, `modifier une ligne du ${P} d'un autre`, false,
                    await tryUpdate(u, entity, l.id, { [spec.editField]: freshText('Modifié') }));
            // (trou trouvé par la preuve : « retirer » n'était pas essayé ici)
            record(actor, entity, `retirer une ligne du ${P} d'un autre`, false, await tryDelete(u, entity, l.id));
            await raw[ps.model].delete({ where: { id: p.id } });
        }

        // 2c. (trous trouvés par la preuve) sur une ligne qu'il gère : sa date de création ne change pas ; ses
        // AUTRES liens se re-désignent vers une fiche qu'il voit (permis), jamais vers une qu'il ne voit pas
        const etatGere = etats.find((s) => dans(c.edit_while, s));
        if (u && c.edit && (!etats.length || etatGere !== undefined) && (!ps.profile || world[`${P}:${u.id}`])) {
            const jetable = !ps.profile;
            const pid = jetable ? (await raw[ps.model].create({ data: ps.build(world, proprio) })).id : world[`${P}:${u.id}`];
            if (jetable && etatGere !== undefined) await setState(P, pid, etatGere);
            const l = await raw[spec.model].create({ data: ligne(pid) });
            record(actor, entity, `changer la date de création d'une ligne`, false,
                await tryUpdate(u, entity, l.id, { createdAt: new Date(2020, 0, 1) }));
            for (const fk of foreignKeys(entity)) {
                const cible = kase.entities[fk.target];
                const visibles: any[] = await as(u)[cible.model].findMany();
                const autre = visibles.find((v) => v[fk.ref] !== l[fk.fk]);
                if (autre) record(actor, entity, `re-désigner ${fk.target} d'une ligne (une fiche qu'il voit)`, true,
                    await tryUpdate(u, entity, l.id, { [fk.fk]: autre[fk.ref] }));
                const cachee = (await raw[cible.model].findMany()).find((t: any) => !visibles.some((v) => v.id === t.id));
                if (cachee) record(actor, entity, `faire pointer une ligne vers un(e) ${fk.target} qu'il ne voit pas`, false,
                    await tryUpdate(u, entity, l.id, { [fk.fk]: cachee[fk.ref] }));
            }
            if (jetable) await raw[ps.model].delete({ where: { id: pid } });
            else await raw[spec.model].deleteMany({ where: { id: l.id } });
        }

        // 3. une ligne ne change jamais de parent, même vers un parent qu'il gère
        if (u && !ps.profile && c.edit) {
            const etatPermis = etats.find((s) => dans(c.edit_while, s));
            const a = await raw[ps.model].create({ data: ps.build(world, proprio) });
            const b = await raw[ps.model].create({ data: ps.build(world, proprio) });
            if (etatPermis) { await setState(P, a.id, etatPermis); await setState(P, b.id, etatPermis); }
            const l = await raw[spec.model].create({ data: ligne(a.id) });
            record(actor, entity, `déplacer une ligne vers un autre ${P}`, false, await tryUpdate(u, entity, l.id, { [fk]: b.id }));
            await raw[ps.model].delete({ where: { id: a.id } });
            await raw[ps.model].delete({ where: { id: b.id } });
        }
    },
};
