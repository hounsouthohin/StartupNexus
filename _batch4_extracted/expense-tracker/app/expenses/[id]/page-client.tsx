"use client";

import { SerializedExpense } from '@/lib/types';

export default function ExpenseDetailClient({ item }: { item: SerializedExpense }) {
  return (
    <div>
      <h1>Détail de la dépense</h1>
      <p><strong>Montant:</strong> {item.amount}€</p>
      <p><strong>Description:</strong> {item.description || 'Aucune description'}</p>
      <p><strong>Catégorie:</strong> {item.category?.name || 'Non catégorisé'}</p>
      <p><strong>Date de création:</strong> {item.createdAt}</p>
    </div>
  );
}
