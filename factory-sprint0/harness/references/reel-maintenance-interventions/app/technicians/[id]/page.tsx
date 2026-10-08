import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import TechniciansIdClient from './page-client'
import { technicianService } from '@/lib/services/technician.service'

export const dynamic = 'force-dynamic'

export default async function TechniciansIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await technicianService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <TechniciansIdClient item={item} />
}
