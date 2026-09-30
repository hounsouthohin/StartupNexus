// AUTO-GÉNÉRÉ PAR dev_seo_generator.py — NE PAS MODIFIER
import type { MetadataRoute } from 'next'

const BASE = process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000'

export const dynamic = 'force-dynamic'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const entries: MetadataRoute.Sitemap = [
    { url: BASE, lastModified: new Date() },
    { url: `${BASE}/run-events`, lastModified: new Date() },
  ]
  return entries
}
