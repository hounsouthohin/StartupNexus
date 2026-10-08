import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ActionsNewClient from './page-client'
import { interventionService } from '@/lib/services/intervention.service'

export const dynamic = 'force-dynamic'

export default async function ActionsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const interventionOptions = await interventionService.getAll(userId)
  return <ActionsNewClient interventionOptions={interventionOptions} />
}
