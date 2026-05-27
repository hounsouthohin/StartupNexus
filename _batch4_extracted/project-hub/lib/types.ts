// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma } from '@prisma/client'
export type { Prisma }
// Types Prisma — disponibles après `prisma generate`
export type { Project, Task, Comment } from '@prisma/client'

export type { ProjectStatus, TaskPriority, TaskStatus } from '@prisma/client'

// Type de réponse API standard — utilise-le dans tous les route handlers
export type ApiResponse<T> = {
  data: T | null
  error: string | null
  success: boolean
}

// Type de réponse paginée
export type PaginatedResponse<T> = ApiResponse<T[]> & {
  total: number
  page: number
  pageSize: number
}

// Types d'entrée pour Project
export type CreateProjectInput = Omit<Prisma.ProjectUncheckedCreateInput, 'createdAt' | 'id' | 'userId'>
export type UpdateProjectInput = Partial<CreateProjectInput>

// Project — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedProject = {
  id: string
  title: string
  description: string | null
  status: "active" | "completed" | "archived"
  createdAt: string
  tasks?: { id: string; title: string; description: string | null; priority: "low" | "medium" | "high"; status: "todo" | "in_progress" | "done"; projectId: string; userId: string; createdAt: string }[]
}

// Types d'entrée pour Task
export type CreateTaskInput = Omit<Prisma.TaskUncheckedCreateInput, 'createdAt' | 'id' | 'userId'>
export type UpdateTaskInput = Partial<CreateTaskInput>

// Task — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedTask = {
  id: string
  title: string
  description: string | null
  priority: "low" | "medium" | "high"
  status: "todo" | "in_progress" | "done"
  projectId: string
  project?: { id: string; title: string; description: string | null; status: "active" | "completed" | "archived"; userId: string; createdAt: string }
  createdAt: string
  comments?: { id: string; content: string; taskId: string; userId: string; createdAt: string }[]
}

// Types d'entrée pour Comment
export type CreateCommentInput = Omit<Prisma.CommentUncheckedCreateInput, 'createdAt' | 'id' | 'userId'>
export type UpdateCommentInput = Partial<CreateCommentInput>

// Comment — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedComment = {
  id: string
  content: string
  taskId: string
  task?: { id: string; title: string; description: string | null; priority: "low" | "medium" | "high"; status: "todo" | "in_progress" | "done"; projectId: string; userId: string; createdAt: string }
  createdAt: string
}

// Paramètres de route pour les pages dynamiques
export type ProjectIdPageParams = { params: { id: string } }
export type TaskIdPageParams = { params: { id: string } }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
