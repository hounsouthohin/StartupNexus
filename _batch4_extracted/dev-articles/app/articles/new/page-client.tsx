"use client";

import React from 'react';
import { SerializedCategory } from '@/lib/types';
import { createArticle } from '../actions';

export default function ArticleCreateClient({ categoryOptions }: { categoryOptions: SerializedCategory[] }) {
  return (
    <form action={createArticle} method="post">
      <div>
        <label htmlFor="title">Title</label>
        <input type="text" id="title" name="title" required />
      </div>
      <div>
        <label htmlFor="content">Content</label>
        <textarea id="content" name="content" required></textarea>
      </div>
      <div>
        <label htmlFor="slug">Slug</label>
        <input type="text" id="slug" name="slug" required />
      </div>
      <div>
        <label htmlFor="status">Status</label>
        <select id="status" name="status">
          <option value="draft">draft</option>
          <option value="published">published</option>
          <option value="archived">archived</option>
        </select>
      </div>
      <div>
        <label htmlFor="categoryId">Category</label>
        <select id="categoryId" name="categoryId">
          {categoryOptions.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </div>
      <button type="submit">Create Article</button>
    </form>
  );
}