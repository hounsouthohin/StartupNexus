"use client";

import React from 'react';
import { SerializedArticle } from '@/lib/types';

export default function ArticleDetailClient({ item }: { item: SerializedArticle }) {
  return (
    <div>
      <h1>{item.title}</h1>
      <p>{item.content}</p>
      <p>Slug: {item.slug}</p>
      <p>Status: {item.status}</p>
      <p>Category: {item.category?.name || 'No category'}</p>
      <p>Created At: {item.createdAt}</p>
    </div>
  );
}