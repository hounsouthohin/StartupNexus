"use client";

import { SerializedCategory } from '@/lib/types';
import { createExpense } from '../actions';
import { useState } from 'react';

export default function ExpenseCreateClient({ categoryOptions }: { categoryOptions: SerializedCategory[] }) {
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState('');

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData();
    formData.set('amount', amount);
    formData.set('description', description);
    formData.set('categoryId', categoryId);
    await createExpense(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="amount">Montant</label>
        <input type="number" id="amount" value={amount} onChange={(e) => setAmount(e.target.value)} required />
      </div>
      <div>
        <label htmlFor="description">Description</label>
        <input type="text" id="description" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>
      <div>
        <label htmlFor="categoryId">Catégorie</label>
        <select id="categoryId" value={categoryId} onChange={(e) => setCategoryId(e.target.value)} required>
          <option value="">Sélectionnez une catégorie</option>
          {categoryOptions.map((category) => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
        </select>
      </div>
      <button type="submit">Créer</button>
    </form>
  );
}
