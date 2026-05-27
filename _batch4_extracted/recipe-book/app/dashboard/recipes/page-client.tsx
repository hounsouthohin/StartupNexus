"use client";

import React from 'react';
import { SerializedRecipe } from '@/lib/types';
import { deleteRecipe } from './actions';
import { useRouter } from 'next/navigation';

export default function RecipeClient({ items }: { items: SerializedRecipe[] }) {
  const router = useRouter();

  const handleDelete = async (id: string) => {
    await deleteRecipe(id);
    router.refresh();
  };

  return (
    <div>
      <h1>Recipes</h1>
      <a href="/dashboard/recipes/new">Nouveau</a>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <h2>{item.title}</h2>
            <p>{item.description}</p>
            <button onClick={() => handleDelete(item.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
