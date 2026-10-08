import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DelaysNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DelaysNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <DelaysNewClient />
}
