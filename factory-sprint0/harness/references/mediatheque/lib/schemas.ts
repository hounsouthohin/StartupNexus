// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Book ──────────────────────────────────────────────────
export const CreateBookSchema = z.object({
  title: z.string().min(1),
  author: z.string().min(1),
  summary: z.string().min(1),
  genre: z.enum(["roman", "essai", "bande_dessinee", "jeunesse"]),
  publicationYear: z.coerce.number().int().nonnegative(),
})

export const UpdateBookSchema = z.object({
  title: z.string().optional(),
  author: z.string().optional(),
  summary: z.string().optional(),
  genre: z.enum(["roman", "essai", "bande_dessinee", "jeunesse"]).optional(),
  publicationYear: z.coerce.number().int().nonnegative().optional(),
})
export type CreateBookInput = z.infer<typeof CreateBookSchema>
export type UpdateBookInput = z.infer<typeof UpdateBookSchema>

// ── Member ──────────────────────────────────────────────────
export const CreateMemberSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  phone: z.string().min(1),
})

export const UpdateMemberSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
  phone: z.string().optional(),
})
export type CreateMemberInput = z.infer<typeof CreateMemberSchema>
export type UpdateMemberInput = z.infer<typeof UpdateMemberSchema>

// ── Borrowing ──────────────────────────────────────────────────
export const CreateBorrowingSchema = z.object({
  bookId: z.string().min(1),
})

export const UpdateBorrowingSchema = z.object({
  status: z.enum(["requested", "accepted", "refused", "returned"]).optional(),
  bookId: z.string().optional(),
})
export type CreateBorrowingInput = z.infer<typeof CreateBorrowingSchema>
export type UpdateBorrowingInput = z.infer<typeof UpdateBorrowingSchema>
