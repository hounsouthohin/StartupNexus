"use client";

import React from 'react';
import { SerializedPost } from '@/lib/types';
import { deletePost } from './actions';
import Link from 'next/link';

export default function DashboardClient({ items }: { items: SerializedPost[] }) {
  return (
    <div>
      <h1>Dashboard</h1>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <h2>{item.title}</h2>
            <p>{item.excerpt}</p>
            <p>Status: {item.status}</p>
            <p>Category: {item.category?.name || 'Uncategorized'}</p>
            <p>Created At: {item.createdAt}</p>
            <button onClick={deletePost.bind(null, item.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
      <Link href="/dashboard/new">
        <a>Nouveau</a>
      </Link>
    </div>
  );
}
