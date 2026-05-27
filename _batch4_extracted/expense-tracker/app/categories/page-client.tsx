"use client";

import { SerializedCategory } from '@/lib/types';
import { deleteCategory } from './actions';
import Link from 'next/link';

export default function CategoriesClient({ items }: { items: SerializedCategory[] }) {
  return (
    <div>
      <h1>Categories</h1>
      <Link href="/categories/new">Nouveau</Link>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <span>{item.name}</span>
            <button onClick={() => deleteCategory(item.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
