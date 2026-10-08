import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ClientsClient from './page-client'
import { clientService } from '@/lib/services/client.service'

export const dynamic = 'force-dynamic'

export default async function ClientsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await clientService.getAllWithRelations(userId)
  return <ClientsClient items={items} />
}
