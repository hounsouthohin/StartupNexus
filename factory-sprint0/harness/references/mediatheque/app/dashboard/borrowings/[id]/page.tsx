import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardBorrowingsIdClient from './page-client'
import { borrowingService } from '@/lib/services/borrowing.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DashboardBorrowingsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'librarian'
    ? await borrowingService.getByIdWithRelationsAsAdmin(id)
    : await borrowingService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardBorrowingsIdClient item={item} />
}
