import SpacesClient from './page-client'
import { spaceService } from '@/lib/services/space.service'

export const dynamic = 'force-dynamic'

export default async function SpacesPage() {
  const items = await spaceService.getPublicAll()
  return <SpacesClient items={items} />
}
