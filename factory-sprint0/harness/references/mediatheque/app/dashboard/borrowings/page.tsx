import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardBorrowingsClient from './page-client'
import { borrowingService } from '@/lib/services/borrowing.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DashboardBorrowingsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'librarian'
    ? await borrowingService.getAllAsAdmin()
    : await borrowingService.getAllWithRelations(userId)
  return <DashboardBorrowingsClient items={items} />
}
