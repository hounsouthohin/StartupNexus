// AUTO-GÉNÉRÉ PAR dev_seed_generator.py — données de démonstration (Preview local).
// JS pur (.mjs) → lancé par `node prisma/seed.mjs`, sans tsx ni build. Dev-only.
// Lancer : DATABASE_URL=... SEED_USER_ID=<votre-id-clerk> node prisma/seed.mjs
// Prisma 7 exige un driver adapter (comme lib/prisma.ts) — un new PrismaClient() nu échoue.
import { PrismaClient } from '@prisma/client'
import { PrismaPg } from '@prisma/adapter-pg'
import { Pool } from 'pg'

const pool = new Pool({ connectionString: process.env.DATABASE_URL })
const adapter = new PrismaPg(pool)
const prisma = new PrismaClient({ adapter })
const OWNER = process.env.SEED_USER_ID ?? 'user_demo'
const OWNER2 = process.env.SEED_USER_ID_2 ?? 'user_demo_2'

async function main() {
  const tuitionFeeRows = []
  tuitionFeeRows.push(await prisma.tuitionFee.create({ data: { userId: OWNER, amount: 42.50, dueDate: new Date(Date.now() + 0 * 86400000), studentId: 'StudentId exemple 1' } }))
  tuitionFeeRows.push(await prisma.tuitionFee.create({ data: { userId: OWNER2, amount: 85.00, dueDate: new Date(Date.now() + 1 * 86400000), studentId: 'StudentId exemple 2' } }))

  const studentRecordRows = []
  studentRecordRows.push(await prisma.studentRecord.create({ data: { userId: OWNER, studentId: 'StudentId exemple 1' } }))
  studentRecordRows.push(await prisma.studentRecord.create({ data: { userId: OWNER2, studentId: 'StudentId exemple 2' } }))

  const courseRows = []
  courseRows.push(await prisma.course.create({ data: { userId: OWNER, name: 'Name exemple 1', description: 'Contenu de démonstration pour Course n°1.', credits: 10, coefficient: 42.50 } }))
  courseRows.push(await prisma.course.create({ data: { userId: OWNER2, name: 'Name exemple 2', description: 'Contenu de démonstration pour Course n°2.', credits: 20, coefficient: 85.00 } }))

  const internshipRows = []
  internshipRows.push(await prisma.internship.create({ data: { userId: OWNER, companyName: 'CompanyName exemple 1', duration: 10, studentId: 'StudentId exemple 1' } }))
  internshipRows.push(await prisma.internship.create({ data: { userId: OWNER2, companyName: 'CompanyName exemple 2', duration: 20, studentId: 'StudentId exemple 2' } }))

  const foreignExchangeRows = []
  foreignExchangeRows.push(await prisma.foreignExchange.create({ data: { userId: OWNER, country: 'Country exemple 1', duration: 10, studentId: 'StudentId exemple 1' } }))
  foreignExchangeRows.push(await prisma.foreignExchange.create({ data: { userId: OWNER2, country: 'Country exemple 2', duration: 20, studentId: 'StudentId exemple 2' } }))

  const projectRows = []
  projectRows.push(await prisma.project.create({ data: { userId: OWNER, title: 'Title exemple 1', description: 'Contenu de démonstration pour Project n°1.', studentId: 'StudentId exemple 1' } }))
  projectRows.push(await prisma.project.create({ data: { userId: OWNER2, title: 'Title exemple 2', description: 'Contenu de démonstration pour Project n°2.', studentId: 'StudentId exemple 2' } }))

  const continuousAssessmentRows = []
  continuousAssessmentRows.push(await prisma.continuousAssessment.create({ data: { userId: OWNER, score: 42.50, courseId: courseRows[0].id, studentId: 'StudentId exemple 1' } }))
  continuousAssessmentRows.push(await prisma.continuousAssessment.create({ data: { userId: OWNER2, score: 85.00, courseId: courseRows[1].id, studentId: 'StudentId exemple 2' } }))

  const examRows = []
  examRows.push(await prisma.exam.create({ data: { userId: OWNER, subject: 'Subject exemple 1', date: new Date(Date.now() + 0 * 86400000), studentId: 'StudentId exemple 1' } }))
  examRows.push(await prisma.exam.create({ data: { userId: OWNER2, subject: 'Subject exemple 2', date: new Date(Date.now() + 1 * 86400000), studentId: 'StudentId exemple 2' } }))

  const defenseRows = []
  defenseRows.push(await prisma.defense.create({ data: { userId: OWNER, topic: 'Topic exemple 1', date: new Date(Date.now() + 0 * 86400000), studentId: 'StudentId exemple 1' } }))
  defenseRows.push(await prisma.defense.create({ data: { userId: OWNER2, topic: 'Topic exemple 2', date: new Date(Date.now() + 1 * 86400000), studentId: 'StudentId exemple 2' } }))

  const annualPlanningRows = []
  annualPlanningRows.push(await prisma.annualPlanning.create({ data: { userId: OWNER, year: 10 } }))
  annualPlanningRows.push(await prisma.annualPlanning.create({ data: { userId: OWNER2, year: 20 } }))

  const roomReservationRows = []
  roomReservationRows.push(await prisma.roomReservation.create({ data: { userId: OWNER, roomId: 'RoomId exemple 1', date: new Date(Date.now() + 0 * 86400000) } }))
  roomReservationRows.push(await prisma.roomReservation.create({ data: { userId: OWNER2, roomId: 'RoomId exemple 2', date: new Date(Date.now() + 1 * 86400000) } }))

  const messageRows = []
  messageRows.push(await prisma.message.create({ data: { userId: OWNER, content: 'Contenu de démonstration pour Message n°1.', senderId: 'SenderId exemple 1', receiverId: 'ReceiverId exemple 1' } }))
  messageRows.push(await prisma.message.create({ data: { userId: OWNER2, content: 'Contenu de démonstration pour Message n°2.', senderId: 'SenderId exemple 2', receiverId: 'ReceiverId exemple 2' } }))

  const forumPostRows = []
  forumPostRows.push(await prisma.forumPost.create({ data: { userId: OWNER, title: 'Title exemple 1', content: 'Contenu de démonstration pour ForumPost n°1.' } }))
  forumPostRows.push(await prisma.forumPost.create({ data: { userId: OWNER2, title: 'Title exemple 2', content: 'Contenu de démonstration pour ForumPost n°2.' } }))

  const circularRows = []
  circularRows.push(await prisma.circular.create({ data: { userId: OWNER, title: 'Title exemple 1', content: 'Contenu de démonstration pour Circular n°1.' } }))
  circularRows.push(await prisma.circular.create({ data: { userId: OWNER2, title: 'Title exemple 2', content: 'Contenu de démonstration pour Circular n°2.' } }))

  const absenceRows = []
  absenceRows.push(await prisma.absence.create({ data: { userId: OWNER, date: new Date(Date.now() + 0 * 86400000), reason: 'Reason exemple 1', studentId: 'StudentId exemple 1' } }))
  absenceRows.push(await prisma.absence.create({ data: { userId: OWNER2, date: new Date(Date.now() + 1 * 86400000), reason: 'Reason exemple 2', studentId: 'StudentId exemple 2' } }))

  const delayRows = []
  delayRows.push(await prisma.delay.create({ data: { userId: OWNER, date: new Date(Date.now() + 0 * 86400000), reason: 'Reason exemple 1', studentId: 'StudentId exemple 1' } }))
  delayRows.push(await prisma.delay.create({ data: { userId: OWNER2, date: new Date(Date.now() + 1 * 86400000), reason: 'Reason exemple 2', studentId: 'StudentId exemple 2' } }))

  const exemptionRows = []
  exemptionRows.push(await prisma.exemption.create({ data: { userId: OWNER, reason: 'Reason exemple 1', studentId: 'StudentId exemple 1' } }))
  exemptionRows.push(await prisma.exemption.create({ data: { userId: OWNER2, reason: 'Reason exemple 2', studentId: 'StudentId exemple 2' } }))

  const gradeRows = []
  gradeRows.push(await prisma.grade.create({ data: { userId: OWNER, value: 42.50, courseId: courseRows[0].id, studentId: 'StudentId exemple 1' } }))
  gradeRows.push(await prisma.grade.create({ data: { userId: OWNER2, value: 85.00, courseId: courseRows[1].id, studentId: 'StudentId exemple 2' } }))

  const timetableRows = []
  timetableRows.push(await prisma.timetable.create({ data: { userId: OWNER, schedule: 'Schedule exemple 1' } }))
  timetableRows.push(await prisma.timetable.create({ data: { userId: OWNER2, schedule: 'Schedule exemple 2' } }))

  const newsRows = []
  newsRows.push(await prisma.news.create({ data: { userId: OWNER, title: 'Title exemple 1', content: 'Contenu de démonstration pour News n°1.' } }))
  newsRows.push(await prisma.news.create({ data: { userId: OWNER2, title: 'Title exemple 2', content: 'Contenu de démonstration pour News n°2.' } }))

  const disciplineRows = []
  disciplineRows.push(await prisma.discipline.create({ data: { userId: OWNER, name: 'Name exemple 1', description: 'Contenu de démonstration pour Discipline n°1.' } }))
  disciplineRows.push(await prisma.discipline.create({ data: { userId: OWNER2, name: 'Name exemple 2', description: 'Contenu de démonstration pour Discipline n°2.' } }))

  const sanctionRows = []
  sanctionRows.push(await prisma.sanction.create({ data: { userId: OWNER, type: 'Type exemple 1', description: 'Contenu de démonstration pour Sanction n°1.', studentId: 'StudentId exemple 1' } }))
  sanctionRows.push(await prisma.sanction.create({ data: { userId: OWNER2, type: 'Type exemple 2', description: 'Contenu de démonstration pour Sanction n°2.', studentId: 'StudentId exemple 2' } }))

  const digitalResourceRows = []
  digitalResourceRows.push(await prisma.digitalResource.create({ data: { userId: OWNER, title: 'Title exemple 1', url: 'https://example.com/digitalResource/1' } }))
  digitalResourceRows.push(await prisma.digitalResource.create({ data: { userId: OWNER2, title: 'Title exemple 2', url: 'https://example.com/digitalResource/2' } }))

  const textbookRows = []
  textbookRows.push(await prisma.textbook.create({ data: { userId: OWNER, title: 'Title exemple 1', content: 'Contenu de démonstration pour Textbook n°1.' } }))
  textbookRows.push(await prisma.textbook.create({ data: { userId: OWNER2, title: 'Title exemple 2', content: 'Contenu de démonstration pour Textbook n°2.' } }))

  const competencyRecordRows = []
  competencyRecordRows.push(await prisma.competencyRecord.create({ data: { userId: OWNER, studentId: 'StudentId exemple 1' } }))
  competencyRecordRows.push(await prisma.competencyRecord.create({ data: { userId: OWNER2, studentId: 'StudentId exemple 2' } }))

  const progressReportRows = []
  progressReportRows.push(await prisma.progressReport.create({ data: { userId: OWNER, content: 'Contenu de démonstration pour ProgressReport n°1.', studentId: 'StudentId exemple 1' } }))
  progressReportRows.push(await prisma.progressReport.create({ data: { userId: OWNER2, content: 'Contenu de démonstration pour ProgressReport n°2.', studentId: 'StudentId exemple 2' } }))

  const sharedAgendaRows = []
  sharedAgendaRows.push(await prisma.sharedAgenda.create({ data: { userId: OWNER } }))
  sharedAgendaRows.push(await prisma.sharedAgenda.create({ data: { userId: OWNER2 } }))

  const dSTPlanningRows = []
  dSTPlanningRows.push(await prisma.dSTPlanning.create({ data: { userId: OWNER, schedule: 'Schedule exemple 1' } }))
  dSTPlanningRows.push(await prisma.dSTPlanning.create({ data: { userId: OWNER2, schedule: 'Schedule exemple 2' } }))

  const resourceReservationRows = []
  resourceReservationRows.push(await prisma.resourceReservation.create({ data: { userId: OWNER, resourceId: digitalResourceRows[0].id, date: new Date(Date.now() + 0 * 86400000) } }))
  resourceReservationRows.push(await prisma.resourceReservation.create({ data: { userId: OWNER2, resourceId: digitalResourceRows[1].id, date: new Date(Date.now() + 1 * 86400000) } }))

  console.log('Seed termine pour l utilisateur', OWNER)
}

main()
  .catch((e) => { console.error(e); process.exit(1) })
  .finally(async () => { await prisma.$disconnect(); await pool.end() })
