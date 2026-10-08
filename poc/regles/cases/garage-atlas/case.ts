import type { Case } from '../../run.ts';

export default {
    matrix: 'garage-atlas',
    roles: ['client', 'owner'],
    entities: {
        ClientProfile: {
            model: 'clientProfile',
            ownerField: 'userId',
            profile: true,
            editField: 'name',
            build: (_w, u) => ({ userId: u!.id, name: `Client ${u!.id}` }),
        },
        Vehicle: {
            model: 'vehicle',
            ownerField: 'ownerId',
            editField: 'plate',
            build: (_w, owner) => ({ ownerId: owner!.id, plate: 'AB-123-CD' }),
        },
        Repair: {
            model: 'repair',
            ownerField: 'ownerId',
            stateField: 'status',
            editField: 'description',
            // (repli : un propriétaire sans véhicule — ex. ancien client devenu patron — reçoit celui du client 1)
            build: (w, owner) => ({ ownerId: owner!.id, vehicleId: w[`vehicle:${owner!.id}`] ?? w['vehicle:client_1'], description: 'Freins' }),
        },
    },
    resetOrder: ['repair', 'vehicle', 'clientProfile'],
    seed: async (raw, users) => {
        const w: Record<string, string> = {};
        for (const u of users.client.slice(0, 2)) {
            await raw.clientProfile.create({ data: { userId: u.id, name: `Client ${u.id}` } });
            const v = await raw.vehicle.create({ data: { ownerId: u.id, plate: `${u.id}-PLAQUE` } });
            w[`vehicle:${u.id}`] = v.id;
            await raw.repair.create({ data: { ownerId: u.id, vehicleId: v.id, description: 'Vidange' } });
        }
        return w;
    },
} satisfies Case;
