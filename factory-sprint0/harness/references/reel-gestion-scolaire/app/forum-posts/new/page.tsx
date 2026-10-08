import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ForumPostsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ForumPostsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <ForumPostsNewClient />
}
