import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { foreignExchangeService } from '@/lib/services/foreign-exchange.service'
import ForeignExchangeEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ForeignExchangeEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await foreignExchangeService.getById(userId, id)
  if (!item) notFound()
  return <ForeignExchangeEditClient item={item} />
}
