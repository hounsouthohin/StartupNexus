"use client";

import { createProject } from '../actions';

export default function ProjectCreateClient() {
  return (
    <form action={createProject}>
      <div>
        <label htmlFor="title">Title</label>
        <input type="text" id="title" name="title" required />
      </div>
      <div>
        <label htmlFor="description">Description</label>
        <textarea id="description" name="description"></textarea>
      </div>
      <div>
        <label htmlFor="status">Status</label>
        <select id="status" name="status">
          <option value="active">active</option>
          <option value="completed">completed</option>
          <option value="archived">archived</option>
        </select>
      </div>
      <button type="submit">Create Project</button>
    </form>
  );
}
