"use client";

import { SerializedExpense } from '@/lib/types';
import { updateExpense } from '../../actions';

export default function ExpenseEditClient({ item }: { item: SerializedExpense }) {
  return (
    <form action={updateExpense.bind(null, item.id)}>
      <div>
        <label htmlFor="amount">Montant</label>
        <input type="number" id="amount" name="amount" defaultValue={item.amount} required />
      </div>
      <div>
        <label htmlFor="description">Description</label>
        <input type="text" id="description" name="description" defaultValue={item.description ?? ''} />
      </div>
      <div>
        <label htmlFor="categoryId">Catégorie</label>
        <input type="text" id="categoryId" name="categoryId" defaultValue={item.categoryId} required />
      </div>
      <button type="submit">Mettre à jour</button>
    </form>
  );
}
