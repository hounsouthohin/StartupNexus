import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { newsService } from '@/lib/services/news.service'
import NewsEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function NewsEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await newsService.getById(userId, id)
  if (!item) notFound()
  return <NewsEditClient item={item} />
}
