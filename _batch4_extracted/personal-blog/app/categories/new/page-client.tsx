"use client";

import React from 'react';
import { createCategory } from '../actions';

export default function CategoryCreateClient() {
  return (
    <form action={createCategory}>
      <div>
        <label htmlFor="name">Name</label>
        <input type="text" name="name" id="name" required />
      </div>
      <button type="submit">Create Category</button>
    </form>
  );
}
