import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ResourceReservationsNewClient from './page-client'
import { digitalResourceService } from '@/lib/services/digital-resource.service'

export const dynamic = 'force-dynamic'

export default async function ResourceReservationsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const digitalResourceOptions = await digitalResourceService.getAll(userId)
  return <ResourceReservationsNewClient digitalResourceOptions={digitalResourceOptions} />
}
