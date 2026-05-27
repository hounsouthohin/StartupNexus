"use client";

import { SerializedTask } from '@/lib/types';
import { deleteTask } from './actions';
import { useRouter } from 'next/navigation';

export default function TasksClient({ items }: { items: SerializedTask[] }) {
  const router = useRouter();

  const handleDelete = async (id: string) => {
    await deleteTask(id);
    router.refresh();
  };

  return (
    <div>
      <h1>Tasks</h1>
      <a href="/tasks/new">Nouveau</a>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <h2>{item.title}</h2>
            <p>{item.description}</p>
            <p>Priority: {item.priority}</p>
            <p>Due Date: {item.dueDate}</p>
            <button onClick={() => handleDelete(item.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
