import type { Case } from '../../run.ts';

export default {
    matrix: 'reel-agence-reservations',
    roles: ['admin', 'gestionnaire', 'prestataire'],
    entities: {
        Rate: { model: 'rate', editField: 'label', build: () => ({ label: 'Tarif été', amount: 90 }) },
        Destination: { model: 'destination', editField: 'name', build: () => ({ name: 'Lisbonne' }) },
        ProviderProfile: {
            model: 'providerProfile',
            ownerField: 'userId',
            profile: true,
            editField: 'name',
            build: (_w, u) => ({ userId: u!.id, name: `Prestataire ${u!.id}` }),
        },
        Customer: {
            model: 'customer',
            ownerField: 'ownerId',
            editField: 'name',
            build: (_w, owner) => ({ ownerId: owner!.id, name: 'Mme Diallo' }),
        },
        Reservation: {
            model: 'reservation',
            ownerField: 'ownerId',
            stateField: 'status',
            editField: 'note',
            createsForSelf: ['gestionnaire'], // « peut aussi lui même faire des réservations pour son compte »
            build: (w, owner) => ({
                ownerId: owner!.id,
                customerId: w[`customer:${owner!.id}`] ?? w['customer:prestataire_1'],
                destinationId: w.destination,
                rateId: w.rate,
            }),
        },
    },
    resetOrder: ['reservation', 'customer', 'providerProfile', 'rate', 'destination'],
    seed: async (raw, users) => {
        const w: Record<string, string> = {};
        w.rate = (await raw.rate.create({ data: { label: 'Tarif standard', amount: 100 } })).id;
        w.destination = (await raw.destination.create({ data: { name: 'Dakar' } })).id;
        await raw.rate.create({ data: { label: 'Tarif groupe', amount: 80 } }); // au moins 2 de chaque sorte
        await raw.destination.create({ data: { name: 'Abidjan' } });
        for (const u of users.prestataire.slice(0, 2)) {
            await raw.providerProfile.create({ data: { userId: u.id, name: `Prestataire ${u.id}` } });
            const c = await raw.customer.create({ data: { ownerId: u.id, name: `Client de ${u.id}` } });
            w[`customer:${u.id}`] = c.id;
            await raw.reservation.create({ data: { ownerId: u.id, customerId: c.id, destinationId: w.destination, rateId: w.rate } });
        }
        // une fiche client sans réservation : invisible du gestionnaire (il ne voit les clients qu'au travers des réservations)
        await raw.customer.create({ data: { ownerId: users.prestataire[0].id, name: 'Client sans réservation' } });
        // une réservation du gestionnaire « pour son compte »
        await raw.reservation.create({
            data: { ownerId: users.gestionnaire[0].id, customerId: w['customer:prestataire_1'], destinationId: w.destination, rateId: w.rate },
        });
        return w;
    },
} satisfies Case;
