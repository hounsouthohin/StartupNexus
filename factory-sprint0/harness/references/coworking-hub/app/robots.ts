// AUTO-GÉNÉRÉ PAR dev_seo_generator.py — NE PAS MODIFIER
import type { MetadataRoute } from 'next'

const BASE = process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/dashboard', '/sign-in', '/sign-up'],
    },
    sitemap: `${BASE}/sitemap.xml`,
  }
}
