import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardProfileClient from './page-client'
import { memberService } from '@/lib/services/member.service'

export const dynamic = 'force-dynamic'

export default async function DashboardProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await memberService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardProfileClient item={item} />
}
