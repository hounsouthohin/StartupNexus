"use client";

import { SerializedLeaveRequest } from '@/lib/types';
import { updateLeaveRequest } from '../../actions';

export default function LeaveRequestEditClient({ item }: { item: SerializedLeaveRequest }) {
  return (
    <form action={updateLeaveRequest.bind(null, item.id)}>
      <div>
        <label htmlFor="startDate">Start Date</label>
        <input type="date" name="startDate" defaultValue={item.startDate} required />
      </div>
      <div>
        <label htmlFor="endDate">End Date</label>
        <input type="date" name="endDate" defaultValue={item.endDate} required />
      </div>
      <div>
        <label htmlFor="reason">Reason</label>
        <textarea name="reason" defaultValue={item.reason ?? ''}></textarea>
      </div>
      <div>
        <label htmlFor="type">Type</label>
        <select name="type" defaultValue={item.type}>
          <option value="annual_leave">annual_leave</option>
          <option value="sick_leave">sick_leave</option>
          <option value="unpaid_leave">unpaid_leave</option>
        </select>
      </div>
      <div>
        <label htmlFor="status">Status</label>
        <select name="status" defaultValue={item.status}>
          <option value="pending">pending</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
        </select>
      </div>
      <button type="submit">Update Leave Request</button>
    </form>
  );
}
