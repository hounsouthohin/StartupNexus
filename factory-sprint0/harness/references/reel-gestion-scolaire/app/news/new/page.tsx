import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import NewsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function NewsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <NewsNewClient />
}
