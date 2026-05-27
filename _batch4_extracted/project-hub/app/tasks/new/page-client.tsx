"use client";

import { SerializedProject } from '@/lib/types';
import { createTask } from '../actions';

export default function TaskCreateClient({ projectOptions }: { projectOptions: SerializedProject[] }) {
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
        <label htmlFor="status">Status</label>
        <select id="status" name="status">
          <option value="todo">todo</option>
          <option value="in_progress">in_progress</option>
          <option value="done">done</option>
        </select>
      </div>
      <div>
        <label htmlFor="projectId">Project</label>
        <select id="projectId" name="projectId" required>
          {projectOptions.map((project) => (
            <option key={project.id} value={project.id}>{project.title}</option>
          ))}
        </select>
      </div>
      <button type="submit">Create Task</button>
    </form>
  );
}
