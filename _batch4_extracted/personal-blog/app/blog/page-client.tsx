"use client";

import React from 'react';
import { SerializedPost } from '@/lib/types';
import Link from 'next/link';

export default function PostClient({ items }: { items: SerializedPost[] }) {
  return (
    <div>
      <h1>Blog Posts</h1>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <h2>{item.title}</h2>
            <p>{item.excerpt}</p>
            <p>Status: {item.status}</p>
            <p>Category: {item.category?.name || 'Uncategorized'}</p>
            <p>Created At: {item.createdAt}</p>
          </li>
        ))}
      </ul>
      <Link href="/dashboard/new">
        <a>Nouveau</a>
      </Link>
    </div>
  );
}
