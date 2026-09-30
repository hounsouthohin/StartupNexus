import WorkshopsClient from './page-client'
import { workshopService } from '@/lib/services/workshop.service'

export const dynamic = 'force-dynamic'

export default async function WorkshopsPage() {
  const items = await workshopService.getPublicAll()
  return <WorkshopsClient items={items} />
}
