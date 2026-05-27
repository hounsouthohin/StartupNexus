"use client";

import React from 'react';
import { SerializedCategory } from '@/lib/types';
import { deleteCategory } from './actions';
import Link from 'next/link';

export default function CategoryClient({ items }: { items: SerializedCategory[] }) {
  return (
    <div>
      <h1>Categories</h1>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <h2>{item.name}</h2>
            <button onClick={deleteCategory.bind(null, item.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
      <Link href="/categories/new">
        <a>Nouveau</a>
      </Link>
    </div>
  );
}
