"use client";

import { SerializedProject } from '@/lib/types';
import { deleteProject } from './actions';
import { useRouter } from 'next/navigation';

export default function ProjectsClient({ items }: { items: SerializedProject[] }) {
  const router = useRouter();

  const handleDelete = async (id: string) => {
    await deleteProject(id);
    router.refresh();
  };

  return (
    <div>
      <h1>Projects</h1>
      <a href="/projects/new">Nouveau</a>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <h2>{item.title}</h2>
            <p>{item.description}</p>
            <p>Status: {item.status}</p>
            <p>Created At: {item.createdAt}</p>
            <button onClick={() => handleDelete(item.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
