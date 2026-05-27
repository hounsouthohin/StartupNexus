"use client";

import { SerializedLeaveRequest } from '@/lib/types';

export default function LeaveRequestDetailClient({ item }: { item: SerializedLeaveRequest }) {
  return (
    <div>
      <h1>Leave Request Detail</h1>
      <p>Start Date: {item.startDate}</p>
      <p>End Date: {item.endDate}</p>
      <p>Reason: {item.reason}</p>
      <p>Type: {item.type}</p>
      <p>Status: {item.status}</p>
      <p>Created At: {item.createdAt}</p>
    </div>
  );
}
