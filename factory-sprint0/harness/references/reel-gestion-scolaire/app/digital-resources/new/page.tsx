import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DigitalResourcesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DigitalResourcesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <DigitalResourcesNewClient />
}
