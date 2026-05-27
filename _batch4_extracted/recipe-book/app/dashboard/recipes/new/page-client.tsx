"use client";

import React from 'react';
import { SerializedCategory } from '@/lib/types';
import { createRecipe } from '../actions';

export default function RecipeCreateClient({ categoryOptions }: { categoryOptions: SerializedCategory[] }) {
  return (
    <form action={createRecipe}>
      <div>
        <label htmlFor="title">Title</label>
        <input type="text" name="title" id="title" required />
      </div>
      <div>
        <label htmlFor="description">Description</label>
        <textarea name="description" id="description" required></textarea>
      </div>
      <div>
        <label htmlFor="slug">Slug</label>
        <input type="text" name="slug" id="slug" required />
      </div>
      <div>
        <label htmlFor="status">Status</label>
        <select name="status" id="status" required>
          <option value="draft">draft</option>
          <option value="published">published</option>
          <option value="archived">archived</option>
        </select>
      </div>
      <div>
        <label htmlFor="categoryId">Category</label>
        <select name="categoryId" id="categoryId" required>
          {categoryOptions.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </div>
      <button type="submit">Create Recipe</button>
    </form>
  );
}
