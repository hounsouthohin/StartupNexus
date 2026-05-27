import { notFound } from 'next/navigation'
import ArticlesSlugClient from './page-client'
import { articleService } from '@/lib/services/article.service'

export const dynamic = 'force-dynamic'

export default async function ArticlesSlugPage({ params }: { params: { slug: string } }) {
  const item = await articleService.getBySlugWithRelations(params.slug)
  if (!item) notFound()
  return <ArticlesSlugClient item={item} />
}
