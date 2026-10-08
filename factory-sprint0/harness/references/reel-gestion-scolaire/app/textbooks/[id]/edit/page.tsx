import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { textbookService } from '@/lib/services/textbook.service'
import TextbookEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TextbookEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await textbookService.getById(userId, id)
  if (!item) notFound()
  return <TextbookEditClient item={item} />
}
