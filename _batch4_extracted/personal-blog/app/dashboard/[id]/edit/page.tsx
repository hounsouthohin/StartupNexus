import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { postService } from '@/lib/services/post.service'
import PostEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function PostEditPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await postService.getById(userId, params.id)
  if (!item) notFound()
  return <PostEditClient item={item} />
}
