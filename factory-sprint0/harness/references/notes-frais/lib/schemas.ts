// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── ExpenseReport ──────────────────────────────────────────────────
export const CreateExpenseReportSchema = z.object({
  title: z.string().min(1),
  amount: z.coerce.number().nonnegative(),
  expenseDate: z.coerce.date(),
  category: z.enum(["transport", "repas", "hébergement", "matériel"]),
  description: z.string().optional(),
})

export const UpdateExpenseReportSchema = z.object({
  title: z.string().optional(),
  amount: z.coerce.number().nonnegative().optional(),
  expenseDate: z.coerce.date().optional(),
  category: z.enum(["transport", "repas", "hébergement", "matériel"]).optional(),
  description: z.string().optional(),
  status: z.enum(["draft", "submitted", "approved", "refused", "reimbursed"]).optional(),
  rejectionReason: z.string().optional(),
})
export type CreateExpenseReportInput = z.infer<typeof CreateExpenseReportSchema>
export type UpdateExpenseReportInput = z.infer<typeof UpdateExpenseReportSchema>
