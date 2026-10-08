// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, MachineSocket, InterventionStatus, ActionStatus } from '@prisma/client'
export type { Prisma, MachineSocket, InterventionStatus, ActionStatus }
// Types Prisma — disponibles après `prisma generate`
export type { Client, Machine, Intervention, Action } from '@prisma/client'

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

// Types d'entrée pour Client
export type CreateClientInput = Omit<Prisma.ClientUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateClientInput = Partial<CreateClientInput>

// Client — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedClient = {
  id: string
  name: string
  email: string
  address: string
  machines?: { id: string; model: string; serialNumber: string; socket: MachineSocket; clientId: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Machine
export type CreateMachineInput = Omit<Prisma.MachineUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateMachineInput = Partial<CreateMachineInput>

// Machine — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedMachine = {
  id: string
  model: string
  serialNumber: string
  socket: MachineSocket
  clientId: string
  client?: { id: string; name: string; email: string; address: string; createdAt: string; updatedAt: string }
  interventions?: { id: string; date: string; status: InterventionStatus; machineId: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Intervention
export type CreateInterventionInput = Omit<Prisma.InterventionUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateInterventionInput = Partial<CreateInterventionInput>

// Intervention — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedIntervention = {
  id: string
  date: string
  status: InterventionStatus
  machineId: string
  machine?: { id: string; model: string; serialNumber: string; socket: MachineSocket; clientId: string; createdAt: string; updatedAt: string }
  actions?: { id: string; description: string; status: ActionStatus; interventionId: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Action
export type CreateActionInput = Omit<Prisma.ActionUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateActionInput = Partial<CreateActionInput>

// Action — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedAction = {
  id: string
  description: string
  status: ActionStatus
  interventionId: string
  intervention?: { id: string; date: string; status: InterventionStatus; machineId: string; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type ClientIdPageParams = { params: Promise<{ id: string }> }
export type MachineIdPageParams = { params: Promise<{ id: string }> }
export type InterventionIdPageParams = { params: Promise<{ id: string }> }
export type ActionIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
