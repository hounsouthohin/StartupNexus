"use client";

import { SerializedTask } from '@/lib/types';
import { updateTask } from '../../actions';

export default function TaskEditClient({ item }: { item: SerializedTask }) {
  return (
    <form action={updateTask.bind(null, item.id)}>
      <div>
        <label htmlFor="title">Title</label>
        <input type="text" id="title" name="title" defaultValue={item.title} required />
      </div>
      <div>
        <label htmlFor="description">Description</label>
        <textarea id="description" name="description" defaultValue={item.description ?? ''}></textarea>
      </div>
      <div>
        <label htmlFor="priority">Priority</label>
        <select id="priority" name="priority" defaultValue={item.priority}>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
      </div>
      <div>
        <label htmlFor="dueDate">Due Date</label>
        <input type="date" id="dueDate" name="dueDate" defaultValue={item.dueDate ?? ''} />
      </div>
      <button type="submit">Update Task</button>
    </form>
  );
}
