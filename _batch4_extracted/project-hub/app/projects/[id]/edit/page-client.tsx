"use client";

import { SerializedProject } from '@/lib/types';
import { updateProject } from '../../actions';

export default function ProjectEditClient({ item }: { item: SerializedProject }) {
  return (
    <form action={updateProject.bind(null, item.id)}>
      <div>
        <label htmlFor="title">Title</label>
        <input type="text" id="title" name="title" defaultValue={item.title} required />
      </div>
      <div>
        <label htmlFor="description">Description</label>
        <textarea id="description" name="description" defaultValue={item.description ?? ''}></textarea>
      </div>
      <div>
        <label htmlFor="status">Status</label>
        <select name="status" defaultValue={item.status}>
          <option value="active">active</option>
          <option value="completed">completed</option>
          <option value="archived">archived</option>
        </select>
      </div>
      <button type="submit">Update Project</button>
    </form>
  );
}
