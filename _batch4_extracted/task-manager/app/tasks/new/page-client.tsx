"use client";

import { createTask } from '../actions';

export default function TaskCreateClient() {
  return (
    <form action={createTask}>
      <div>
        <label htmlFor="title">Title</label>
        <input type="text" id="title" name="title" required />
      </div>
      <div>
        <label htmlFor="description">Description</label>
        <textarea id="description" name="description"></textarea>
      </div>
      <div>
        <label htmlFor="priority">Priority</label>
        <select id="priority" name="priority">
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
      </div>
      <div>
        <label htmlFor="dueDate">Due Date</label>
        <input type="date" id="dueDate" name="dueDate" />
      </div>
      <button type="submit">Create Task</button>
    </form>
  );
}
