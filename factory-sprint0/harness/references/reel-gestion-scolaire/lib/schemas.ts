// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── TuitionFee ──────────────────────────────────────────────────
export const CreateTuitionFeeSchema = z.object({
  amount: z.coerce.number().nonnegative(),
  dueDate: z.coerce.date(),
  studentId: z.string().min(1),
})

export const UpdateTuitionFeeSchema = z.object({
  amount: z.coerce.number().nonnegative().optional(),
  dueDate: z.coerce.date().optional(),
  studentId: z.string().optional(),
})
export type CreateTuitionFeeInput = z.infer<typeof CreateTuitionFeeSchema>
export type UpdateTuitionFeeInput = z.infer<typeof UpdateTuitionFeeSchema>

// ── StudentRecord ──────────────────────────────────────────────────
export const CreateStudentRecordSchema = z.object({
  studentId: z.string().min(1),
  courseIds: z.array(z.string()).optional(),
  internshipIds: z.array(z.string()).optional(),
  foreignExchangeIds: z.array(z.string()).optional(),
  projectIds: z.array(z.string()).optional(),
  continuousAssessmentIds: z.array(z.string()).optional(),
  examIds: z.array(z.string()).optional(),
  defenseIds: z.array(z.string()).optional(),
})

export const UpdateStudentRecordSchema = z.object({
  studentId: z.string().optional(),
  courseIds: z.array(z.string()).optional(),
  internshipIds: z.array(z.string()).optional(),
  foreignExchangeIds: z.array(z.string()).optional(),
  projectIds: z.array(z.string()).optional(),
  continuousAssessmentIds: z.array(z.string()).optional(),
  examIds: z.array(z.string()).optional(),
  defenseIds: z.array(z.string()).optional(),
})
export type CreateStudentRecordInput = z.infer<typeof CreateStudentRecordSchema>
export type UpdateStudentRecordInput = z.infer<typeof UpdateStudentRecordSchema>

// ── Course ──────────────────────────────────────────────────
export const CreateCourseSchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
  credits: z.coerce.number().int().nonnegative(),
  coefficient: z.coerce.number(),
})

export const UpdateCourseSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  credits: z.coerce.number().int().nonnegative().optional(),
  coefficient: z.coerce.number().optional(),
})
export type CreateCourseInput = z.infer<typeof CreateCourseSchema>
export type UpdateCourseInput = z.infer<typeof UpdateCourseSchema>

// ── Internship ──────────────────────────────────────────────────
export const CreateInternshipSchema = z.object({
  companyName: z.string().min(1),
  duration: z.coerce.number().int().nonnegative(),
  studentId: z.string().min(1),
})

export const UpdateInternshipSchema = z.object({
  companyName: z.string().optional(),
  duration: z.coerce.number().int().nonnegative().optional(),
  studentId: z.string().optional(),
})
export type CreateInternshipInput = z.infer<typeof CreateInternshipSchema>
export type UpdateInternshipInput = z.infer<typeof UpdateInternshipSchema>

// ── ForeignExchange ──────────────────────────────────────────────────
export const CreateForeignExchangeSchema = z.object({
  country: z.string().min(1),
  duration: z.coerce.number().int().nonnegative(),
  studentId: z.string().min(1),
})

export const UpdateForeignExchangeSchema = z.object({
  country: z.string().optional(),
  duration: z.coerce.number().int().nonnegative().optional(),
  studentId: z.string().optional(),
})
export type CreateForeignExchangeInput = z.infer<typeof CreateForeignExchangeSchema>
export type UpdateForeignExchangeInput = z.infer<typeof UpdateForeignExchangeSchema>

// ── Project ──────────────────────────────────────────────────
export const CreateProjectSchema = z.object({
  title: z.string().min(1),
  description: z.string().optional(),
  studentId: z.string().min(1),
})

export const UpdateProjectSchema = z.object({
  title: z.string().optional(),
  description: z.string().optional(),
  studentId: z.string().optional(),
})
export type CreateProjectInput = z.infer<typeof CreateProjectSchema>
export type UpdateProjectInput = z.infer<typeof UpdateProjectSchema>

// ── ContinuousAssessment ──────────────────────────────────────────────────
export const CreateContinuousAssessmentSchema = z.object({
  score: z.coerce.number(),
  studentId: z.string().min(1),
  courseId: z.string().min(1),
})

export const UpdateContinuousAssessmentSchema = z.object({
  score: z.coerce.number().optional(),
  studentId: z.string().optional(),
  courseId: z.string().optional(),
})
export type CreateContinuousAssessmentInput = z.infer<typeof CreateContinuousAssessmentSchema>
export type UpdateContinuousAssessmentInput = z.infer<typeof UpdateContinuousAssessmentSchema>

// ── Exam ──────────────────────────────────────────────────
export const CreateExamSchema = z.object({
  subject: z.string().min(1),
  date: z.coerce.date(),
  studentId: z.string().min(1),
})

export const UpdateExamSchema = z.object({
  subject: z.string().optional(),
  date: z.coerce.date().optional(),
  studentId: z.string().optional(),
})
export type CreateExamInput = z.infer<typeof CreateExamSchema>
export type UpdateExamInput = z.infer<typeof UpdateExamSchema>

// ── Defense ──────────────────────────────────────────────────
export const CreateDefenseSchema = z.object({
  topic: z.string().min(1),
  date: z.coerce.date(),
  studentId: z.string().min(1),
})

export const UpdateDefenseSchema = z.object({
  topic: z.string().optional(),
  date: z.coerce.date().optional(),
  studentId: z.string().optional(),
})
export type CreateDefenseInput = z.infer<typeof CreateDefenseSchema>
export type UpdateDefenseInput = z.infer<typeof UpdateDefenseSchema>

// ── AnnualPlanning ──────────────────────────────────────────────────
export const CreateAnnualPlanningSchema = z.object({
  year: z.coerce.number().int().nonnegative(),
})

export const UpdateAnnualPlanningSchema = z.object({
  year: z.coerce.number().int().nonnegative().optional(),
})
export type CreateAnnualPlanningInput = z.infer<typeof CreateAnnualPlanningSchema>
export type UpdateAnnualPlanningInput = z.infer<typeof UpdateAnnualPlanningSchema>

// ── RoomReservation ──────────────────────────────────────────────────
export const CreateRoomReservationSchema = z.object({
  roomId: z.string().min(1),
  date: z.coerce.date(),
})

export const UpdateRoomReservationSchema = z.object({
  roomId: z.string().optional(),
  date: z.coerce.date().optional(),
})
export type CreateRoomReservationInput = z.infer<typeof CreateRoomReservationSchema>
export type UpdateRoomReservationInput = z.infer<typeof UpdateRoomReservationSchema>

// ── Message ──────────────────────────────────────────────────
export const CreateMessageSchema = z.object({
  content: z.string().min(1),
  senderId: z.string().min(1),
  receiverId: z.string().min(1),
})

export const UpdateMessageSchema = z.object({
  content: z.string().optional(),
  senderId: z.string().optional(),
  receiverId: z.string().optional(),
})
export type CreateMessageInput = z.infer<typeof CreateMessageSchema>
export type UpdateMessageInput = z.infer<typeof UpdateMessageSchema>

// ── ForumPost ──────────────────────────────────────────────────
export const CreateForumPostSchema = z.object({
  title: z.string().min(1),
  content: z.string().min(1),
})

export const UpdateForumPostSchema = z.object({
  title: z.string().optional(),
  content: z.string().optional(),
})
export type CreateForumPostInput = z.infer<typeof CreateForumPostSchema>
export type UpdateForumPostInput = z.infer<typeof UpdateForumPostSchema>

// ── Circular ──────────────────────────────────────────────────
export const CreateCircularSchema = z.object({
  title: z.string().min(1),
  content: z.string().min(1),
})

export const UpdateCircularSchema = z.object({
  title: z.string().optional(),
  content: z.string().optional(),
})
export type CreateCircularInput = z.infer<typeof CreateCircularSchema>
export type UpdateCircularInput = z.infer<typeof UpdateCircularSchema>

// ── Absence ──────────────────────────────────────────────────
export const CreateAbsenceSchema = z.object({
  date: z.coerce.date(),
  reason: z.string().optional(),
  studentId: z.string().min(1),
})

export const UpdateAbsenceSchema = z.object({
  date: z.coerce.date().optional(),
  reason: z.string().optional(),
  studentId: z.string().optional(),
})
export type CreateAbsenceInput = z.infer<typeof CreateAbsenceSchema>
export type UpdateAbsenceInput = z.infer<typeof UpdateAbsenceSchema>

// ── Delay ──────────────────────────────────────────────────
export const CreateDelaySchema = z.object({
  date: z.coerce.date(),
  reason: z.string().optional(),
  studentId: z.string().min(1),
})

export const UpdateDelaySchema = z.object({
  date: z.coerce.date().optional(),
  reason: z.string().optional(),
  studentId: z.string().optional(),
})
export type CreateDelayInput = z.infer<typeof CreateDelaySchema>
export type UpdateDelayInput = z.infer<typeof UpdateDelaySchema>

// ── Exemption ──────────────────────────────────────────────────
export const CreateExemptionSchema = z.object({
  reason: z.string().min(1),
  studentId: z.string().min(1),
})

export const UpdateExemptionSchema = z.object({
  reason: z.string().optional(),
  studentId: z.string().optional(),
})
export type CreateExemptionInput = z.infer<typeof CreateExemptionSchema>
export type UpdateExemptionInput = z.infer<typeof UpdateExemptionSchema>

// ── Grade ──────────────────────────────────────────────────
export const CreateGradeSchema = z.object({
  value: z.coerce.number(),
  studentId: z.string().min(1),
  courseId: z.string().min(1),
})

export const UpdateGradeSchema = z.object({
  value: z.coerce.number().optional(),
  studentId: z.string().optional(),
  courseId: z.string().optional(),
})
export type CreateGradeInput = z.infer<typeof CreateGradeSchema>
export type UpdateGradeInput = z.infer<typeof UpdateGradeSchema>

// ── Timetable ──────────────────────────────────────────────────
export const CreateTimetableSchema = z.object({
  schedule: z.string().min(1),
})

export const UpdateTimetableSchema = z.object({
  schedule: z.string().optional(),
})
export type CreateTimetableInput = z.infer<typeof CreateTimetableSchema>
export type UpdateTimetableInput = z.infer<typeof UpdateTimetableSchema>

// ── ResourceReservation ──────────────────────────────────────────────────
export const CreateResourceReservationSchema = z.object({
  date: z.coerce.date(),
  resourceId: z.string().min(1),
})

export const UpdateResourceReservationSchema = z.object({
  date: z.coerce.date().optional(),
  resourceId: z.string().optional(),
})
export type CreateResourceReservationInput = z.infer<typeof CreateResourceReservationSchema>
export type UpdateResourceReservationInput = z.infer<typeof UpdateResourceReservationSchema>

// ── News ──────────────────────────────────────────────────
export const CreateNewsSchema = z.object({
  title: z.string().min(1),
  content: z.string().min(1),
})

export const UpdateNewsSchema = z.object({
  title: z.string().optional(),
  content: z.string().optional(),
})
export type CreateNewsInput = z.infer<typeof CreateNewsSchema>
export type UpdateNewsInput = z.infer<typeof UpdateNewsSchema>

// ── Discipline ──────────────────────────────────────────────────
export const CreateDisciplineSchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
})

export const UpdateDisciplineSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
})
export type CreateDisciplineInput = z.infer<typeof CreateDisciplineSchema>
export type UpdateDisciplineInput = z.infer<typeof UpdateDisciplineSchema>

// ── Sanction ──────────────────────────────────────────────────
export const CreateSanctionSchema = z.object({
  type: z.string().min(1),
  description: z.string().optional(),
  studentId: z.string().min(1),
})

export const UpdateSanctionSchema = z.object({
  type: z.string().optional(),
  description: z.string().optional(),
  studentId: z.string().optional(),
})
export type CreateSanctionInput = z.infer<typeof CreateSanctionSchema>
export type UpdateSanctionInput = z.infer<typeof UpdateSanctionSchema>

// ── DigitalResource ──────────────────────────────────────────────────
export const CreateDigitalResourceSchema = z.object({
  title: z.string().min(1),
  url: z.string().url(),
})

export const UpdateDigitalResourceSchema = z.object({
  title: z.string().optional(),
  url: z.string().url().optional(),
})
export type CreateDigitalResourceInput = z.infer<typeof CreateDigitalResourceSchema>
export type UpdateDigitalResourceInput = z.infer<typeof UpdateDigitalResourceSchema>

// ── Textbook ──────────────────────────────────────────────────
export const CreateTextbookSchema = z.object({
  title: z.string().min(1),
  content: z.string().min(1),
})

export const UpdateTextbookSchema = z.object({
  title: z.string().optional(),
  content: z.string().optional(),
})
export type CreateTextbookInput = z.infer<typeof CreateTextbookSchema>
export type UpdateTextbookInput = z.infer<typeof UpdateTextbookSchema>

// ── CompetencyRecord ──────────────────────────────────────────────────
export const CreateCompetencyRecordSchema = z.object({
  studentId: z.string().min(1),
})

export const UpdateCompetencyRecordSchema = z.object({
  studentId: z.string().optional(),
})
export type CreateCompetencyRecordInput = z.infer<typeof CreateCompetencyRecordSchema>
export type UpdateCompetencyRecordInput = z.infer<typeof UpdateCompetencyRecordSchema>

// ── ProgressReport ──────────────────────────────────────────────────
export const CreateProgressReportSchema = z.object({
  content: z.string().min(1),
  studentId: z.string().min(1),
})

export const UpdateProgressReportSchema = z.object({
  content: z.string().optional(),
  studentId: z.string().optional(),
})
export type CreateProgressReportInput = z.infer<typeof CreateProgressReportSchema>
export type UpdateProgressReportInput = z.infer<typeof UpdateProgressReportSchema>

// ── SharedAgenda ──────────────────────────────────────────────────
export const CreateSharedAgendaSchema = z.object({
  // aucun champ mutable détecté
})

export const UpdateSharedAgendaSchema = z.object({
  // aucun champ mutable
})
export type CreateSharedAgendaInput = z.infer<typeof CreateSharedAgendaSchema>
export type UpdateSharedAgendaInput = z.infer<typeof UpdateSharedAgendaSchema>

// ── DSTPlanning ──────────────────────────────────────────────────
export const CreateDSTPlanningSchema = z.object({
  schedule: z.string().min(1),
})

export const UpdateDSTPlanningSchema = z.object({
  schedule: z.string().optional(),
})
export type CreateDSTPlanningInput = z.infer<typeof CreateDSTPlanningSchema>
export type UpdateDSTPlanningInput = z.infer<typeof UpdateDSTPlanningSchema>
