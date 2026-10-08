import type { Case } from '../../run.ts';

export default {
    matrix: 'notes-frais',
    roles: ['employee', 'manager'],
    entities: {
        ExpenseReport: {
            model: 'expenseReport',
            ownerField: 'ownerId',
            stateField: 'status',
            editField: 'label',
            build: (_w, owner) => ({ label: 'Taxi', amount: 30, ownerId: owner!.id }),
        },
    },
    resetOrder: ['expenseReport'],
    seed: async (raw, users) => {
        for (const u of users.employee.slice(0, 2))
            for (const label of ['Train', 'Hôtel'])
                await raw.expenseReport.create({ data: { label, amount: 100, ownerId: u.id } });
        return {};
    },
} satisfies Case;
