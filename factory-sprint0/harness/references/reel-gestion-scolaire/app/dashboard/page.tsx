import Link from 'next/link'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { tuitionFeeService } from '@/lib/services/tuition-fee.service'
import { studentRecordService } from '@/lib/services/student-record.service'
import { courseService } from '@/lib/services/course.service'
import { internshipService } from '@/lib/services/internship.service'
import { foreignExchangeService } from '@/lib/services/foreign-exchange.service'
import { projectService } from '@/lib/services/project.service'
import { continuousAssessmentService } from '@/lib/services/continuous-assessment.service'
import { examService } from '@/lib/services/exam.service'
import { defenseService } from '@/lib/services/defense.service'
import { annualPlanningService } from '@/lib/services/annual-planning.service'
import { roomReservationService } from '@/lib/services/room-reservation.service'
import { messageService } from '@/lib/services/message.service'
import { forumPostService } from '@/lib/services/forum-post.service'
import { circularService } from '@/lib/services/circular.service'
import { absenceService } from '@/lib/services/absence.service'
import { delayService } from '@/lib/services/delay.service'
import { exemptionService } from '@/lib/services/exemption.service'
import { gradeService } from '@/lib/services/grade.service'
import { timetableService } from '@/lib/services/timetable.service'
import { resourceReservationService } from '@/lib/services/resource-reservation.service'
import { newsService } from '@/lib/services/news.service'
import { disciplineService } from '@/lib/services/discipline.service'
import { sanctionService } from '@/lib/services/sanction.service'
import { digitalResourceService } from '@/lib/services/digital-resource.service'
import { textbookService } from '@/lib/services/textbook.service'
import { competencyRecordService } from '@/lib/services/competency-record.service'
import { progressReportService } from '@/lib/services/progress-report.service'
import { sharedAgendaService } from '@/lib/services/shared-agenda.service'
import { dSTPlanningService } from '@/lib/services/d-s-t-planning.service'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const [tuitionFeeItems, studentRecordItems, courseItems, internshipItems, foreignExchangeItems, projectItems, continuousAssessmentItems, examItems, defenseItems, annualPlanningItems, roomReservationItems, messageItems, forumPostItems, circularItems, absenceItems, delayItems, exemptionItems, gradeItems, timetableItems, resourceReservationItems, newsItems, disciplineItems, sanctionItems, digitalResourceItems, textbookItems, competencyRecordItems, progressReportItems, sharedAgendaItems, dSTPlanningItems] = await Promise.all([
    tuitionFeeService.getAll(userId, 1, 100000),
    studentRecordService.getAll(userId, 1, 100000),
    courseService.getAll(userId, 1, 100000),
    internshipService.getAll(userId, 1, 100000),
    foreignExchangeService.getAll(userId, 1, 100000),
    projectService.getAll(userId, 1, 100000),
    continuousAssessmentService.getAll(userId, 1, 100000),
    examService.getAll(userId, 1, 100000),
    defenseService.getAll(userId, 1, 100000),
    annualPlanningService.getAll(userId, 1, 100000),
    roomReservationService.getAll(userId, 1, 100000),
    messageService.getAll(userId, 1, 100000),
    forumPostService.getAll(userId, 1, 100000),
    circularService.getAll(userId, 1, 100000),
    absenceService.getAll(userId, 1, 100000),
    delayService.getAll(userId, 1, 100000),
    exemptionService.getAll(userId, 1, 100000),
    gradeService.getAll(userId, 1, 100000),
    timetableService.getAll(userId, 1, 100000),
    resourceReservationService.getAll(userId, 1, 100000),
    newsService.getAll(userId, 1, 100000),
    disciplineService.getAll(userId, 1, 100000),
    sanctionService.getAll(userId, 1, 100000),
    digitalResourceService.getAll(userId, 1, 100000),
    textbookService.getAll(userId, 1, 100000),
    competencyRecordService.getAll(userId, 1, 100000),
    progressReportService.getAll(userId, 1, 100000),
    sharedAgendaService.getAll(userId, 1, 100000),
    dSTPlanningService.getAll(userId, 1, 100000),
  ])

  const tuitionFeeCount = tuitionFeeItems.length
  const studentRecordCount = studentRecordItems.length
  const courseCount = courseItems.length
  const internshipCount = internshipItems.length
  const foreignExchangeCount = foreignExchangeItems.length
  const projectCount = projectItems.length
  const continuousAssessmentCount = continuousAssessmentItems.length
  const examCount = examItems.length
  const defenseCount = defenseItems.length
  const annualPlanningCount = annualPlanningItems.length
  const roomReservationCount = roomReservationItems.length
  const messageCount = messageItems.length
  const forumPostCount = forumPostItems.length
  const circularCount = circularItems.length
  const absenceCount = absenceItems.length
  const delayCount = delayItems.length
  const exemptionCount = exemptionItems.length
  const gradeCount = gradeItems.length
  const timetableCount = timetableItems.length
  const resourceReservationCount = resourceReservationItems.length
  const newsCount = newsItems.length
  const disciplineCount = disciplineItems.length
  const sanctionCount = sanctionItems.length
  const digitalResourceCount = digitalResourceItems.length
  const textbookCount = textbookItems.length
  const competencyRecordCount = competencyRecordItems.length
  const progressReportCount = progressReportItems.length
  const sharedAgendaCount = sharedAgendaItems.length
  const dSTPlanningCount = dSTPlanningItems.length

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Frais de scolarité</p>
          <p className="text-3xl font-bold text-foreground mb-4">{tuitionFeeCount}</p>
          <Link href="/tuition-fees" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Dossiers scolaires</p>
          <p className="text-3xl font-bold text-foreground mb-4">{studentRecordCount}</p>
          <Link href="/student-records" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Cours</p>
          <p className="text-3xl font-bold text-foreground mb-4">{courseCount}</p>
          <Link href="/courses" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Stages</p>
          <p className="text-3xl font-bold text-foreground mb-4">{internshipCount}</p>
          <Link href="/internships" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Séjours à l'étranger</p>
          <p className="text-3xl font-bold text-foreground mb-4">{foreignExchangeCount}</p>
          <Link href="/foreign-exchanges" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Projets</p>
          <p className="text-3xl font-bold text-foreground mb-4">{projectCount}</p>
          <Link href="/projects" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Contrôles continus</p>
          <p className="text-3xl font-bold text-foreground mb-4">{continuousAssessmentCount}</p>
          <Link href="/continuous-assessments" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Examens</p>
          <p className="text-3xl font-bold text-foreground mb-4">{examCount}</p>
          <Link href="/exams" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Soutenances</p>
          <p className="text-3xl font-bold text-foreground mb-4">{defenseCount}</p>
          <Link href="/defenses" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Planifications annuelles</p>
          <p className="text-3xl font-bold text-foreground mb-4">{annualPlanningCount}</p>
          <Link href="/annual-plannings" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Réservations de locaux</p>
          <p className="text-3xl font-bold text-foreground mb-4">{roomReservationCount}</p>
          <Link href="/room-reservations" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Messages</p>
          <p className="text-3xl font-bold text-foreground mb-4">{messageCount}</p>
          <Link href="/messages" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Messages du forum</p>
          <p className="text-3xl font-bold text-foreground mb-4">{forumPostCount}</p>
          <Link href="/forum-posts" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Circulaires</p>
          <p className="text-3xl font-bold text-foreground mb-4">{circularCount}</p>
          <Link href="/circulars" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Absences</p>
          <p className="text-3xl font-bold text-foreground mb-4">{absenceCount}</p>
          <Link href="/absences" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Retards</p>
          <p className="text-3xl font-bold text-foreground mb-4">{delayCount}</p>
          <Link href="/delays" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Dispenses</p>
          <p className="text-3xl font-bold text-foreground mb-4">{exemptionCount}</p>
          <Link href="/exemptions" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Notes</p>
          <p className="text-3xl font-bold text-foreground mb-4">{gradeCount}</p>
          <Link href="/grades" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Emplois du temps</p>
          <p className="text-3xl font-bold text-foreground mb-4">{timetableCount}</p>
          <Link href="/timetables" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Réservations de ressources</p>
          <p className="text-3xl font-bold text-foreground mb-4">{resourceReservationCount}</p>
          <Link href="/resource-reservations" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Actualités</p>
          <p className="text-3xl font-bold text-foreground mb-4">{newsCount}</p>
          <Link href="/news" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Disciplines</p>
          <p className="text-3xl font-bold text-foreground mb-4">{disciplineCount}</p>
          <Link href="/disciplines" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Sanctions</p>
          <p className="text-3xl font-bold text-foreground mb-4">{sanctionCount}</p>
          <Link href="/sanctions" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Ressources numériques</p>
          <p className="text-3xl font-bold text-foreground mb-4">{digitalResourceCount}</p>
          <Link href="/digital-resources" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Cahiers de textes</p>
          <p className="text-3xl font-bold text-foreground mb-4">{textbookCount}</p>
          <Link href="/textbooks" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Livrets de compétences</p>
          <p className="text-3xl font-bold text-foreground mb-4">{competencyRecordCount}</p>
          <Link href="/competency-records" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Carnets de suivi</p>
          <p className="text-3xl font-bold text-foreground mb-4">{progressReportCount}</p>
          <Link href="/progress-reports" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Agendas partagés</p>
          <p className="text-3xl font-bold text-foreground mb-4">{sharedAgendaCount}</p>
          <Link href="/shared-agendas" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Planifications D.S.T</p>
          <p className="text-3xl font-bold text-foreground mb-4">{dSTPlanningCount}</p>
          <Link href="/dst-plannings" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
      </div>
    </main>
  )
}
