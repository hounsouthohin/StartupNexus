import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ProjectsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ProjectsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <ProjectsNewClient />
}
