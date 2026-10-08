import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { circularService } from '@/lib/services/circular.service'
import CircularEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function CircularEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await circularService.getById(userId, id)
  if (!item) notFound()
  return <CircularEditClient item={item} />
}
