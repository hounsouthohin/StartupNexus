"use client";

import React from 'react';
import Link from 'next/link';
import { SerializedArticle } from '@/lib/types';

export default function ArticlesClient({ items }: { items: SerializedArticle[] }) {
  return (
    <div>
      <h1>Articles</h1>
      <Link href="/articles/new">
        <a>Nouveau</a>
      </Link>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <h2>{item.title}</h2>
            <p>{item.content}</p>
            <p>Status: {item.status}</p>
            <p>Category: {item.category?.name || 'No category'}</p>
            <p>Created At: {item.createdAt}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}