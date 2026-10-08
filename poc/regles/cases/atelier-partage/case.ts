import type { Case } from '../../run.ts';

export default {
    matrix: 'atelier-partage',
    roles: ['participant', 'animateur'],
    entities: {
        Workshop: {
            model: 'workshop',
            editField: 'title',
            build: () => ({ title: 'Céramique' }),
        },
        Domain: {
            model: 'domain',
            editField: 'name',
            build: () => ({ name: 'Couture' }),
        },
        Slot: {
            model: 'slot',
            editField: 'label',
            build: (w) => ({ workshopId: w.workshop, label: 'Samedi 10 h' }),
        },
        ParticipantProfile: {
            model: 'participantProfile',
            ownerField: 'userId',
            profile: true,
            editField: 'name',
            build: (_w, u) => ({ userId: u!.id, name: `Participant ${u!.id}` }),
        },
        Reservation: {
            model: 'reservation',
            ownerField: 'ownerId',
            stateField: 'status',
            editField: 'comment',
            build: (w, owner) => ({ ownerId: owner!.id, slotId: w.slot }),
        },
    },
    resetOrder: ['reservation', 'participantProfile', 'slot', 'workshop', 'domain'],
    seed: async (raw, users) => {
        const dessin = await raw.domain.create({ data: { name: 'Dessin' } });
        await raw.domain.create({ data: { name: 'Poterie' } }); // aucun atelier : pas visible du visiteur
        const workshop = await raw.workshop.create({ data: { title: 'Croquis', domains: { connect: [{ id: dessin.id }] } } });
        const slot = await raw.slot.create({ data: { workshopId: workshop.id, label: 'Mardi 18 h' } });
        await raw.slot.create({ data: { workshopId: workshop.id, label: 'Jeudi 14 h' } }); // au moins 2 de chaque sorte
        for (const u of users.participant.slice(0, 2)) {
            await raw.participantProfile.create({ data: { userId: u.id, name: `Participant ${u.id}` } });
            await raw.reservation.create({ data: { ownerId: u.id, slotId: slot.id } });
        }
        await raw.participantProfile.create({ data: { userId: 'participant_sans_reservation', name: 'Sans réservation' } });
        return { workshop: workshop.id, slot: slot.id };
    },
} satisfies Case;
