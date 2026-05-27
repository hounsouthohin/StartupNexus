"use client";

import React from 'react';
import { SerializedCategory } from '@/lib/types';
import { createPost } from '../actions';

export default function PostCreateClient({ categoryOptions }: { categoryOptions: SerializedCategory[] }) {
  return (
    <form action={createPost}>
      <div>
        <label htmlFor="title">Title</label>
        <input type="text" name="title" id="title" required />
      </div>
      <div>
        <label htmlFor="excerpt">Excerpt</label>
        <textarea name="excerpt" id="excerpt" required></textarea>
      </div>
      <div>
        <label htmlFor="status">Status</label>
        <select name="status" id="status">
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>
      </div>
      <div>
        <label htmlFor="categoryId">Category</label>
        <select name="categoryId" id="categoryId">
          {categoryOptions.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </div>
      <button type="submit">Create Post</button>
    </form>
  );
}
