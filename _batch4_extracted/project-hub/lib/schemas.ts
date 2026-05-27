// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Project ──────────────────────────────────────────────────
export const CreateProjectSchema = z.object({
  title: z.string(),
  description: z.string().optional(),
  status: z.enum(["active", "completed", "archived"]).optional(),
})

export const UpdateProjectSchema = CreateProjectSchema.partial()
export type CreateProjectInput = z.infer<typeof CreateProjectSchema>
export type UpdateProjectInput = z.infer<typeof UpdateProjectSchema>

// ── Task ──────────────────────────────────────────────────
export const CreateTaskSchema = z.object({
  title: z.string(),
  description: z.string().optional(),
  priority: z.enum(["low", "medium", "high"]).optional(),
  status: z.enum(["todo", "in_progress", "done"]).optional(),
  projectId: z.string(),
})

export const UpdateTaskSchema = CreateTaskSchema.partial()
export type CreateTaskInput = z.infer<typeof CreateTaskSchema>
export type UpdateTaskInput = z.infer<typeof UpdateTaskSchema>

// ── Comment ──────────────────────────────────────────────────
export const CreateCommentSchema = z.object({
  content: z.string(),
  taskId: z.string(),
})

export const UpdateCommentSchema = CreateCommentSchema.partial()
export type CreateCommentInput = z.infer<typeof CreateCommentSchema>
export type UpdateCommentInput = z.infer<typeof UpdateCommentSchema>
