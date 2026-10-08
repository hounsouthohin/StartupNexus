import type { Case } from '../../run.ts';

export default {
    matrix: 'reel-sav-depannage',
    roles: ['staff'],
    entities: {
        Customer: { model: 'customer', editField: 'name', build: () => ({ name: 'M. Ouédraogo' }) },
        SocketType: { model: 'socketType', editField: 'label', build: () => ({ label: '1151' }) },
        Machine: {
            model: 'machine',
            editField: 'model',
            build: (w) => ({ customerId: w.customer, model: 'Tour Dell', socketTypeId: w.socket }),
        },
        Intervention: {
            model: 'intervention',
            stateField: 'status',
            editField: 'summary',
            build: (w) => ({ machineId: w.machine, summary: "Ne démarre plus" }),
        },
        Action: {
            model: 'action',
            stateField: 'status',
            editField: 'label',
            build: (w) => ({ interventionId: w.intervention, label: 'Changer l’alimentation' }),
        },
    },
    resetOrder: ['action', 'intervention', 'machine', 'customer', 'socketType'],
    seed: async (raw) => {
        const sockets = [];
        for (const label of ['478', '754', '775', 'AM2']) sockets.push(await raw.socketType.create({ data: { label } }));
        const customer = await raw.customer.create({ data: { name: 'Mme Sawadogo' } });
        const machine = await raw.machine.create({ data: { customerId: customer.id, model: 'Portable HP', socketTypeId: sockets[0].id } });
        await raw.machine.create({ data: { customerId: customer.id, model: 'Imprimante' } }); // sans socket : lien facultatif
        const intervention = await raw.intervention.create({ data: { machineId: machine.id, summary: 'Écran noir' } });
        await raw.action.create({ data: { interventionId: intervention.id, label: 'Diagnostic' } });
        await raw.intervention.create({ data: { machineId: machine.id, summary: 'Ventilateur bruyant' } }); // au moins 2 de chaque sorte
        return { customer: customer.id, machine: machine.id, intervention: intervention.id, socket: sockets[1].id };
    },
} satisfies Case;
