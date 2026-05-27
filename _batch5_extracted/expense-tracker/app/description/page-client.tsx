"use client";

import { useState } from 'react';

export default function DescriptionPageClient() {
  const [description, setDescription] = useState('');

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Description</h1>
      <textarea
        className="w-full p-2 border rounded"
        rows={4}
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Enter description here..."
      />
      <p className="mt-2 text-gray-600">{description}</p>
    </div>
  );
}
