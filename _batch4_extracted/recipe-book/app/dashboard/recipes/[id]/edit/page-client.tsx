"use client";

import React from 'react';
import { SerializedRecipe } from '@/lib/types';
import { updateRecipe } from '../../actions';

export default function RecipeEditClient({ item }: { item: SerializedRecipe }) {
  return (
    <form action={updateRecipe.bind(null, item.id)}>
      <div>
        <label htmlFor="title">Title</label>
        <input type="text" name="title" id="title" defaultValue={item.title} required />
      </div>
      <div>
        <label htmlFor="description">Description</label>
        <textarea name="description" id="description" defaultValue={item.description} required></textarea>
      </div>
      <div>
        <label htmlFor="slug">Slug</label>
        <input type="text" name="slug" id="slug" defaultValue={item.slug} required />
      </div>
      <div>
        <label htmlFor="status">Status</label>
        <select name="status" defaultValue={item.status} required>
          <option value="draft">draft</option>
          <option value="published">published</option>
          <option value="archived">archived</option>
        </select>
      </div>
      <div>
        <label htmlFor="categoryId">Category</label>
        <input type="text" name="categoryId" id="categoryId" defaultValue={item.categoryId} required />
      </div>
      <button type="submit">Update Recipe</button>
    </form>
  );
}
