import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import NewsIdClient from './page-client'
import { newsService } from '@/lib/services/news.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function NewsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await newsService.getByIdAsAdmin(id)
    : await newsService.getById(userId, id)
  if (!item) notFound()
  return <NewsIdClient item={item} />
}
