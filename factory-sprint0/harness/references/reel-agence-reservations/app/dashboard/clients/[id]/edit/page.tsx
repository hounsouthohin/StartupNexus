import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { clientService } from '@/lib/services/client.service'
import ClientEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ClientEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await clientService.getById(userId, id)
  if (!item) notFound()
  return <ClientEditClient item={item} />
}
