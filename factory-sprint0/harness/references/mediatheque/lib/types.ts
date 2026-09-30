// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, BookGenre, BorrowingStatus } from '@prisma/client'
export type { Prisma, BookGenre, BorrowingStatus }
// Types Prisma — disponibles après `prisma generate`
export type { Book, Member, Borrowing } from '@prisma/client'

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

// Types d'entrée pour Book
export type CreateBookInput = Omit<Prisma.BookUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateBookInput = Partial<CreateBookInput>

// Book — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedBook = {
  id: string
  title: string
  author: string
  summary: string
  genre: BookGenre
  publicationYear: number
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Member
export type CreateMemberInput = Omit<Prisma.MemberUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateMemberInput = Partial<CreateMemberInput>

// Member — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedMember = {
  id: string
  name: string
  email: string
  phone: string
  createdAt: string
  updatedAt: string
  borrowings?: { id: string; requestDate: string; status: BorrowingStatus; bookId: string; createdAt: string; updatedAt: string }[]
}

// Types d'entrée pour Borrowing
export type CreateBorrowingInput = Omit<Prisma.BorrowingUncheckedCreateInput, 'createdAt' | 'id' | 'requestDate' | 'updatedAt' | 'userId'>
export type UpdateBorrowingInput = Partial<CreateBorrowingInput>

// Borrowing — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedBorrowing = {
  id: string
  requestDate: string
  status: BorrowingStatus
  bookId: string
  book?: { id: string; title: string; author: string; summary: string; genre: BookGenre; publicationYear: number; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type BookIdPageParams = { params: Promise<{ id: string }> }
export type BorrowingIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
