// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, SubscriptionStatus } from '@prisma/client'
export type { Prisma, SubscriptionStatus }
// Types Prisma — disponibles après `prisma generate`
export type { Member, Subscription, Course, Reservation, Payment } from '@prisma/client'

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

// Types d'entrée pour Member
export type CreateMemberInput = Omit<Prisma.MemberUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateMemberInput = Partial<CreateMemberInput>

// Member — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedMember = {
  id: string
  subscriptionId: string | null
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Subscription
export type CreateSubscriptionInput = Omit<Prisma.SubscriptionUncheckedCreateInput, 'createdAt' | 'id' | 'memberId' | 'updatedAt'>
export type UpdateSubscriptionInput = Partial<CreateSubscriptionInput>

// Subscription — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedSubscription = {
  id: string
  status: SubscriptionStatus
  renewalDate: string
  member?: { id: string; subscriptionId: string | null; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Course
export type CreateCourseInput = Omit<Prisma.CourseUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateCourseInput = Partial<CreateCourseInput>

// Course — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedCourse = {
  id: string
  title: string
  description: string | null
  schedule: string
  createdAt: string
  updatedAt: string
  reservations?: { id: string; memberId: string; createdAt: string; updatedAt: string }[]
}

// Types d'entrée pour Reservation
export type CreateReservationInput = Omit<Prisma.ReservationUncheckedCreateInput, 'courseId' | 'createdAt' | 'id' | 'updatedAt'>
export type UpdateReservationInput = Partial<CreateReservationInput>

// Reservation — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedReservation = {
  id: string
  course?: { id: string; title: string; description: string | null; schedule: string; createdAt: string; updatedAt: string }
  memberId: string
  member?: { id: string; subscriptionId: string | null; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Payment
export type CreatePaymentInput = Omit<Prisma.PaymentUncheckedCreateInput, 'createdAt' | 'id' | 'subscriptionId' | 'updatedAt'>
export type UpdatePaymentInput = Partial<CreatePaymentInput>

// Payment — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedPayment = {
  id: string
  amount: number
  date: string
  subscription?: { id: string; status: SubscriptionStatus; renewalDate: string; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type MemberIdPageParams = { params: Promise<{ id: string }> }
export type SubscriptionIdPageParams = { params: Promise<{ id: string }> }
export type CourseIdPageParams = { params: Promise<{ id: string }> }
export type ReservationIdPageParams = { params: Promise<{ id: string }> }
export type PaymentIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
