"use client";

import React from 'react';
import { SerializedPost } from '@/lib/types';
import { updatePost } from '../../actions';

export default function PostEditClient({ item }: { item: SerializedPost }) {
  return (
    <form action={updatePost.bind(null, item.id)}>
      <div>
        <label htmlFor="title">Title</label>
        <input type="text" name="title" id="title" defaultValue={item.title} required />
      </div>
      <div>
        <label htmlFor="excerpt">Excerpt</label>
        <textarea name="excerpt" id="excerpt" defaultValue={item.excerpt} required />
      </div>
      <div>
        <label htmlFor="status">Status</label>
        <select name="status" defaultValue={item.status}>
          <option value="draft">draft</option>
          <option value="published">published</option>
        </select>
      </div>
      <button type="submit">Update Post</button>
    </form>
  );
}
