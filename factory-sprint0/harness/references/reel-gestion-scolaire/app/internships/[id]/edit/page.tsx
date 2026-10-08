import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { internshipService } from '@/lib/services/internship.service'
import InternshipEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function InternshipEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await internshipService.getById(userId, id)
  if (!item) notFound()
  return <InternshipEditClient item={item} />
}
