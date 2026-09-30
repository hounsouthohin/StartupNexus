import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardSubscriptionsNewClient from './page-client'
import { categoryService } from '@/lib/services/category.service'

export const dynamic = 'force-dynamic'

export default async function DashboardSubscriptionsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const categoryOptions = await categoryService.getAll(userId)
  return <DashboardSubscriptionsNewClient categoryOptions={categoryOptions} />
}
