import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import TextbooksIdClient from './page-client'
import { textbookService } from '@/lib/services/textbook.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function TextbooksIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await textbookService.getByIdAsAdmin(id)
    : await textbookService.getById(userId, id)
  if (!item) notFound()
  return <TextbooksIdClient item={item} />
}
