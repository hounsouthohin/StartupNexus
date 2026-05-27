"use client";

import React from 'react';
import { SerializedPost } from '@/lib/types';

export default function PostDetailClient({ item }: { item: SerializedPost }) {
  return (
    <div>
      <h1>{item.title}</h1>
      <p>{item.excerpt}</p>
      <p>Status: {item.status}</p>
      <p>Category: {item.category?.name || 'Uncategorized'}</p>
      <p>Created At: {item.createdAt}</p>
    </div>
  );
}
