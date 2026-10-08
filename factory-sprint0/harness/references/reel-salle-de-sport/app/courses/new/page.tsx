import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import CoursesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function CoursesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <CoursesNewClient />
}
