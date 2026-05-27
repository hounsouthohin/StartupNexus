"use client";

import { SerializedLeaveRequest } from '@/lib/types';
import { deleteLeaveRequest } from './actions';
import { useRouter } from 'next/navigation';

export default function LeaveRequestsClient({ items }: { items: SerializedLeaveRequest[] }) {
  const router = useRouter();

  const handleDelete = async (id: string) => {
    await deleteLeaveRequest(id);
    router.refresh();
  };

  return (
    <div>
      <h1>Leave Requests</h1>
      <a href="/leave-requests/new">Nouveau</a>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <p>Start Date: {item.startDate}</p>
            <p>End Date: {item.endDate}</p>
            <p>Reason: {item.reason}</p>
            <p>Type: {item.type}</p>
            <p>Status: {item.status}</p>
            <button onClick={() => handleDelete(item.id)}>Supprimer</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
