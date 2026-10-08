import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TextbooksClient from './page-client'
import { textbookService } from '@/lib/services/textbook.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function TextbooksPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await textbookService.getAllAsAdmin()
    : await textbookService.getAll(userId)
  return <TextbooksClient items={items} />
}
