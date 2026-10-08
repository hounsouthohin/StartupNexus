import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TuitionFeesClient from './page-client'
import { tuitionFeeService } from '@/lib/services/tuition-fee.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function TuitionFeesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await tuitionFeeService.getAllAsAdmin()
    : await tuitionFeeService.getAllWithRelations(userId)
  return <TuitionFeesClient items={items} />
}
