import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ExamsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ExamsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <ExamsNewClient />
}
