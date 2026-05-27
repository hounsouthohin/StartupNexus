import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardClient from './page-client'
import { postService } from '@/lib/services/post.service'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await postService.getAllWithRelations(userId)
  return <DashboardClient items={items} />
}
