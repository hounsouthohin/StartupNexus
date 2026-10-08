import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { tuitionFeeService } from '@/lib/services/tuition-fee.service'
import TuitionFeeEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TuitionFeeEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await tuitionFeeService.getById(userId, id)
  if (!item) notFound()
  return <TuitionFeeEditClient item={item} />
}
