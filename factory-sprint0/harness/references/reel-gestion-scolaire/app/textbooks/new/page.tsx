import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TextbooksNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TextbooksNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <TextbooksNewClient />
}
