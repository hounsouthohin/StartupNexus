"use client";

import { SerializedTask } from '@/lib/types';

export default function TaskDetailClient({ item }: { item: SerializedTask }) {
  return (
    <div>
      <h1>{item.title}</h1>
      <p>{item.description}</p>
      <p>Priority: {item.priority}</p>
      <p>Due Date: {item.dueDate}</p>
      <p>Created At: {item.createdAt}</p>
    </div>
  );
}
