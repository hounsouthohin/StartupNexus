"use client";

import React from 'react';
import { SerializedRecipe } from '@/lib/types';

export default function RecipeDetailClient({ item }: { item: SerializedRecipe }) {
  return (
    <div>
      <h1>{item.title}</h1>
      <p>{item.description}</p>
      <p>Slug: {item.slug}</p>
      <p>Status: {item.status}</p>
      <p>Category ID: {item.categoryId}</p>
      {item.category && (
        <div>
          <h2>Category Details</h2>
          <p>Name: {item.category.name}</p>
          <p>User ID: {item.category.userId}</p>
          <p>Created At: {item.category.createdAt}</p>
        </div>
      )}
      <p>Created At: {item.createdAt}</p>
    </div>
  );
}
