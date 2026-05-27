"use client";

import { SerializedProject } from '@/lib/types';

export default function ProjectDetailClient({ item }: { item: SerializedProject }) {
  return (
    <div>
      <h1>{item.title}</h1>
      <p>{item.description}</p>
      <p>Status: {item.status}</p>
      <p>Created At: {item.createdAt}</p>
    </div>
  );
}
