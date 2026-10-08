// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma } from '@prisma/client'
export type { Prisma }
// Types Prisma — disponibles après `prisma generate`
export type { TuitionFee, StudentRecord, Course, Internship, ForeignExchange, Project, ContinuousAssessment, Exam, Defense, AnnualPlanning, RoomReservation, Message, ForumPost, Circular, Absence, Delay, Exemption, Grade, Timetable, ResourceReservation, News, Discipline, Sanction, DigitalResource, Textbook, CompetencyRecord, ProgressReport, SharedAgenda, DSTPlanning } from '@prisma/client'

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

// Types d'entrée pour TuitionFee
export type CreateTuitionFeeInput = Omit<Prisma.TuitionFeeUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateTuitionFeeInput = Partial<CreateTuitionFeeInput>

// TuitionFee — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedTuitionFee = {
  id: string
  amount: number
  dueDate: string
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour StudentRecord
export type CreateStudentRecordInput = Omit<Prisma.StudentRecordUncheckedCreateInput, 'continuousAssessments' | 'courses' | 'createdAt' | 'defenses' | 'exams' | 'foreignExchanges' | 'id' | 'internships' | 'projects' | 'updatedAt' | 'userId'> & { courseIds?: string[] } & { internshipIds?: string[] } & { foreignExchangeIds?: string[] } & { projectIds?: string[] } & { continuousAssessmentIds?: string[] } & { examIds?: string[] } & { defenseIds?: string[] }
export type UpdateStudentRecordInput = Partial<CreateStudentRecordInput>

// StudentRecord — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedStudentRecord = {
  id: string
  studentId: string
  student?: { id: string; [key: string]: unknown }
  courses?: { id: string; name: string; description: string | null; credits: number; coefficient: number; createdAt: string; updatedAt: string }[]
  internships?: { id: string; companyName: string; duration: number; studentId: string; createdAt: string; updatedAt: string }[]
  foreignExchanges?: { id: string; country: string; duration: number; studentId: string; createdAt: string; updatedAt: string }[]
  projects?: { id: string; title: string; description: string | null; studentId: string; createdAt: string; updatedAt: string }[]
  continuousAssessments?: { id: string; score: number; courseId: string; studentId: string; createdAt: string; updatedAt: string }[]
  exams?: { id: string; subject: string; date: string; studentId: string; createdAt: string; updatedAt: string }[]
  defenses?: { id: string; topic: string; date: string; studentId: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Course
export type CreateCourseInput = Omit<Prisma.CourseUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateCourseInput = Partial<CreateCourseInput>

// Course — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedCourse = {
  id: string
  name: string
  description: string | null
  credits: number
  coefficient: number
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Internship
export type CreateInternshipInput = Omit<Prisma.InternshipUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateInternshipInput = Partial<CreateInternshipInput>

// Internship — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedInternship = {
  id: string
  companyName: string
  duration: number
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour ForeignExchange
export type CreateForeignExchangeInput = Omit<Prisma.ForeignExchangeUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateForeignExchangeInput = Partial<CreateForeignExchangeInput>

// ForeignExchange — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedForeignExchange = {
  id: string
  country: string
  duration: number
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Project
export type CreateProjectInput = Omit<Prisma.ProjectUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateProjectInput = Partial<CreateProjectInput>

// Project — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedProject = {
  id: string
  title: string
  description: string | null
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour ContinuousAssessment
export type CreateContinuousAssessmentInput = Omit<Prisma.ContinuousAssessmentUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateContinuousAssessmentInput = Partial<CreateContinuousAssessmentInput>

// ContinuousAssessment — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedContinuousAssessment = {
  id: string
  score: number
  courseId: string
  course?: { id: string; name: string; description: string | null; credits: number; coefficient: number; createdAt: string; updatedAt: string }
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Exam
export type CreateExamInput = Omit<Prisma.ExamUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateExamInput = Partial<CreateExamInput>

// Exam — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedExam = {
  id: string
  subject: string
  date: string
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Defense
export type CreateDefenseInput = Omit<Prisma.DefenseUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateDefenseInput = Partial<CreateDefenseInput>

// Defense — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedDefense = {
  id: string
  topic: string
  date: string
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour AnnualPlanning
export type CreateAnnualPlanningInput = Omit<Prisma.AnnualPlanningUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateAnnualPlanningInput = Partial<CreateAnnualPlanningInput>

// AnnualPlanning — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedAnnualPlanning = {
  id: string
  year: number
  events: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour RoomReservation
export type CreateRoomReservationInput = Omit<Prisma.RoomReservationUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateRoomReservationInput = Partial<CreateRoomReservationInput>

// RoomReservation — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedRoomReservation = {
  id: string
  roomId: string
  room?: { id: string; [key: string]: unknown }
  date: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Message
export type CreateMessageInput = Omit<Prisma.MessageUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateMessageInput = Partial<CreateMessageInput>

// Message — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedMessage = {
  id: string
  content: string
  senderId: string
  receiverId: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour ForumPost
export type CreateForumPostInput = Omit<Prisma.ForumPostUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateForumPostInput = Partial<CreateForumPostInput>

// ForumPost — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedForumPost = {
  id: string
  title: string
  content: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Circular
export type CreateCircularInput = Omit<Prisma.CircularUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateCircularInput = Partial<CreateCircularInput>

// Circular — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedCircular = {
  id: string
  title: string
  content: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Absence
export type CreateAbsenceInput = Omit<Prisma.AbsenceUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateAbsenceInput = Partial<CreateAbsenceInput>

// Absence — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedAbsence = {
  id: string
  date: string
  reason: string | null
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Delay
export type CreateDelayInput = Omit<Prisma.DelayUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateDelayInput = Partial<CreateDelayInput>

// Delay — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedDelay = {
  id: string
  date: string
  reason: string | null
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Exemption
export type CreateExemptionInput = Omit<Prisma.ExemptionUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateExemptionInput = Partial<CreateExemptionInput>

// Exemption — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedExemption = {
  id: string
  reason: string
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Grade
export type CreateGradeInput = Omit<Prisma.GradeUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateGradeInput = Partial<CreateGradeInput>

// Grade — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedGrade = {
  id: string
  value: number
  courseId: string
  course?: { id: string; name: string; description: string | null; credits: number; coefficient: number; createdAt: string; updatedAt: string }
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Timetable
export type CreateTimetableInput = Omit<Prisma.TimetableUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateTimetableInput = Partial<CreateTimetableInput>

// Timetable — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedTimetable = {
  id: string
  schedule: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour ResourceReservation
export type CreateResourceReservationInput = Omit<Prisma.ResourceReservationUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateResourceReservationInput = Partial<CreateResourceReservationInput>

// ResourceReservation — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedResourceReservation = {
  id: string
  resourceId: string
  resource?: { id: string; [key: string]: unknown }
  date: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour News
export type CreateNewsInput = Omit<Prisma.NewsUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateNewsInput = Partial<CreateNewsInput>

// News — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedNews = {
  id: string
  title: string
  content: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Discipline
export type CreateDisciplineInput = Omit<Prisma.DisciplineUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateDisciplineInput = Partial<CreateDisciplineInput>

// Discipline — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedDiscipline = {
  id: string
  name: string
  description: string | null
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Sanction
export type CreateSanctionInput = Omit<Prisma.SanctionUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateSanctionInput = Partial<CreateSanctionInput>

// Sanction — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedSanction = {
  id: string
  type: string
  description: string | null
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour DigitalResource
export type CreateDigitalResourceInput = Omit<Prisma.DigitalResourceUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateDigitalResourceInput = Partial<CreateDigitalResourceInput>

// DigitalResource — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedDigitalResource = {
  id: string
  title: string
  url: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Textbook
export type CreateTextbookInput = Omit<Prisma.TextbookUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateTextbookInput = Partial<CreateTextbookInput>

// Textbook — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedTextbook = {
  id: string
  title: string
  content: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour CompetencyRecord
export type CreateCompetencyRecordInput = Omit<Prisma.CompetencyRecordUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateCompetencyRecordInput = Partial<CreateCompetencyRecordInput>

// CompetencyRecord — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedCompetencyRecord = {
  id: string
  competencies: string
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour ProgressReport
export type CreateProgressReportInput = Omit<Prisma.ProgressReportUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateProgressReportInput = Partial<CreateProgressReportInput>

// ProgressReport — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedProgressReport = {
  id: string
  content: string
  studentId: string
  student?: { id: string; [key: string]: unknown }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour SharedAgenda
export type CreateSharedAgendaInput = Omit<Prisma.SharedAgendaUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateSharedAgendaInput = Partial<CreateSharedAgendaInput>

// SharedAgenda — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedSharedAgenda = {
  id: string
  events: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour DSTPlanning
export type CreateDSTPlanningInput = Omit<Prisma.DSTPlanningUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateDSTPlanningInput = Partial<CreateDSTPlanningInput>

// DSTPlanning — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedDSTPlanning = {
  id: string
  schedule: string
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type DynamicIdPageParams = { params: Promise<{ id: string }> }
export type CourseIdPageParams = { params: Promise<{ id: string }> }
export type InternshipIdPageParams = { params: Promise<{ id: string }> }
export type ProjectIdPageParams = { params: Promise<{ id: string }> }
export type ExamIdPageParams = { params: Promise<{ id: string }> }
export type DefenseIdPageParams = { params: Promise<{ id: string }> }
export type MessageIdPageParams = { params: Promise<{ id: string }> }
export type CircularIdPageParams = { params: Promise<{ id: string }> }
export type AbsenceIdPageParams = { params: Promise<{ id: string }> }
export type DelayIdPageParams = { params: Promise<{ id: string }> }
export type ExemptionIdPageParams = { params: Promise<{ id: string }> }
export type GradeIdPageParams = { params: Promise<{ id: string }> }
export type TimetableIdPageParams = { params: Promise<{ id: string }> }
export type NewsIdPageParams = { params: Promise<{ id: string }> }
export type DisciplineIdPageParams = { params: Promise<{ id: string }> }
export type SanctionIdPageParams = { params: Promise<{ id: string }> }
export type TextbookIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
