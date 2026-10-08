import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import NewsClient from './page-client'
import { newsService } from '@/lib/services/news.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function NewsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await newsService.getAllAsAdmin()
    : await newsService.getAll(userId)
  return <NewsClient items={items} />
}
