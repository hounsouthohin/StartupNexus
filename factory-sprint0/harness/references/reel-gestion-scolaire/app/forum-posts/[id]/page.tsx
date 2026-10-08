import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ForumPostsIdClient from './page-client'
import { forumPostService } from '@/lib/services/forum-post.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ForumPostsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await forumPostService.getByIdAsAdmin(id)
    : await forumPostService.getById(userId, id)
  if (!item) notFound()
  return <ForumPostsIdClient item={item} />
}
