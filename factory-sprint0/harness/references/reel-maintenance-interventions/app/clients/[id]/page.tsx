import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ClientsIdClient from './page-client'
import { clientService } from '@/lib/services/client.service'

export const dynamic = 'force-dynamic'

export default async function ClientsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await clientService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <ClientsIdClient item={item} />
}
