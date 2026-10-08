import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { forumPostService } from '@/lib/services/forum-post.service'
import ForumPostEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ForumPostEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await forumPostService.getById(userId, id)
  if (!item) notFound()
  return <ForumPostEditClient item={item} />
}
