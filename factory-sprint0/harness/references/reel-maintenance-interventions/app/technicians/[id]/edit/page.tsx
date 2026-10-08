import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { technicianService } from '@/lib/services/technician.service'
import TechnicianEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TechnicianEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await technicianService.getById(userId, id)
  if (!item) notFound()
  return <TechnicianEditClient item={item} />
}
