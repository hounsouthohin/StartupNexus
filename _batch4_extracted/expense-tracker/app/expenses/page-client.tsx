"use client";

import { SerializedExpense } from '@/lib/types';
import { deleteExpense } from './actions';
import Link from 'next/link';

export default function ExpensesClient({ items }: { items: SerializedExpense[] }) {
  return (
    <div>
      <h1>Expenses</h1>
      <Link href="/expenses/new">Nouveau</Link>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <span>{item.description} - {item.amount}€</span>
            <button onClick={() => deleteExpense(item.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
