"use client";

import React from 'react';
import { SerializedCategory } from '@/lib/types';
import { updateCategory } from '../../actions';

export default function CategoryEditClient({ item }: { item: SerializedCategory }) {
  return (
    <form action={updateCategory.bind(null, item.id)}>
      <div>
        <label htmlFor="name">Name</label>
        <input type="text" name="name" id="name" defaultValue={item.name} required />
      </div>
      <button type="submit">Update Category</button>
    </form>
  );
}
