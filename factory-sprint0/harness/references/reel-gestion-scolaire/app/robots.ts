// AUTO-GÉNÉRÉ PAR dev_seo_generator.py — NE PAS MODIFIER
import type { MetadataRoute } from 'next'

const BASE = process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/tuition-fees', '/student-records', '/courses', '/internships', '/foreign-exchanges', '/projects', '/continuous-assessments', '/exams', '/defenses', '/annual-plannings', '/room-reservations', '/messages', '/forum-posts', '/circulars', '/absences', '/delays', '/exemptions', '/grades', '/timetables', '/resource-reservations', '/news', '/disciplines', '/sanctions', '/digital-resources', '/textbooks', '/competency-records', '/progress-reports', '/shared-agendas', '/dst-plannings', '/sign-in', '/sign-up'],
    },
    sitemap: `${BASE}/sitemap.xml`,
  }
}
