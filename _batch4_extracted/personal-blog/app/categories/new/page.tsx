import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import CategoriesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function CategoriesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <CategoriesNewClient />
}
