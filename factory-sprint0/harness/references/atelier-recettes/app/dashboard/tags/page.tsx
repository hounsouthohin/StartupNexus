import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardTagsClient from './page-client'
import { tagService } from '@/lib/services/tag.service'

export const dynamic = 'force-dynamic'

export default async function DashboardTagsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await tagService.getAllWithRelations(userId)
  return <DashboardTagsClient items={items} />
}
