import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { exemptionService } from '@/lib/services/exemption.service'
import ExemptionEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ExemptionEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await exemptionService.getById(userId, id)
  if (!item) notFound()
  return <ExemptionEditClient item={item} />
}
