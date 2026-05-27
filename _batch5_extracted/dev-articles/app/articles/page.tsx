import ArticlesClient from './page-client'
import { articleService } from '@/lib/services/article.service'

export const dynamic = 'force-dynamic'

export default async function ArticlesPage() {
  const items = await articleService.getPublished()
  return <ArticlesClient items={items} />
}
