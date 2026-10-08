import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DstPlanningsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DstPlanningsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <DstPlanningsNewClient />
}
