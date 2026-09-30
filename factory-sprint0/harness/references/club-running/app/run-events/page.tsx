import RunEventsClient from './page-client'
import { runEventService } from '@/lib/services/run-event.service'

export const dynamic = 'force-dynamic'

export default async function RunEventsPage() {
  const items = await runEventService.getPublicAll()
  return <RunEventsClient items={items} />
}
