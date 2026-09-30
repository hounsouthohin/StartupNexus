import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardRecipesNewClient from './page-client'
import { tagService } from '@/lib/services/tag.service'

export const dynamic = 'force-dynamic'

export default async function DashboardRecipesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const tagOptions = await tagService.getAll(userId)
  return <DashboardRecipesNewClient tagOptions={tagOptions} />
}
