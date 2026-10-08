import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { delayService } from '@/lib/services/delay.service'
import DelayEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DelayEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await delayService.getById(userId, id)
  if (!item) notFound()
  return <DelayEditClient item={item} />
}
