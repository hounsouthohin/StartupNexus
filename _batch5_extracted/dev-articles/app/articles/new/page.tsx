import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ArticlesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ArticlesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <ArticlesNewClient />
}
