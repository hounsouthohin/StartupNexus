import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ForumPostsClient from './page-client'
import { forumPostService } from '@/lib/services/forum-post.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ForumPostsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await forumPostService.getAllAsAdmin()
    : await forumPostService.getAll(userId)
  return <ForumPostsClient items={items} />
}
