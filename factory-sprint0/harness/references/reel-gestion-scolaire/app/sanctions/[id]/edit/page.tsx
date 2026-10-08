import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { sanctionService } from '@/lib/services/sanction.service'
import SanctionEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function SanctionEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await sanctionService.getById(userId, id)
  if (!item) notFound()
  return <SanctionEditClient item={item} />
}
