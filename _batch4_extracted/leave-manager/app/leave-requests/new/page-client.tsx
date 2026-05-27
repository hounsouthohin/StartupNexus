"use client";

import { createLeaveRequest } from '../actions';

export default function LeaveRequestCreateClient() {
  return (
    <form action={createLeaveRequest}>
      <div>
        <label htmlFor="startDate">Start Date</label>
        <input type="date" name="startDate" required />
      </div>
      <div>
        <label htmlFor="endDate">End Date</label>
        <input type="date" name="endDate" required />
      </div>
      <div>
        <label htmlFor="reason">Reason</label>
        <textarea name="reason"></textarea>
      </div>
      <div>
        <label htmlFor="type">Type</label>
        <select name="type">
          <option value="annual_leave">annual_leave</option>
          <option value="sick_leave">sick_leave</option>
          <option value="unpaid_leave">unpaid_leave</option>
        </select>
      </div>
      <div>
        <label htmlFor="status">Status</label>
        <select name="status">
          <option value="pending">pending</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
        </select>
      </div>
      <button type="submit">Create Leave Request</button>
    </form>
  );
}
