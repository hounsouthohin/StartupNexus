import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { examService } from '@/lib/services/exam.service'
import ExamEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ExamEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await examService.getById(userId, id)
  if (!item) notFound()
  return <ExamEditClient item={item} />
}
