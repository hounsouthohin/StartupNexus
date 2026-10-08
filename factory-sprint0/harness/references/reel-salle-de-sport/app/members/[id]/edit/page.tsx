import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { memberService } from '@/lib/services/member.service'
import { subscriptionService } from '@/lib/services/subscription.service'
import MemberEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function MemberEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await memberService.getById(userId, id)
  if (!item) notFound()
  const subscriptionOptions = await subscriptionService.getAll(userId)
  return <MemberEditClient item={item} subscriptionOptions={subscriptionOptions} />
}
