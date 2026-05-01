// AUTO-GÉNÉRÉ PAR factory stack nextjs-clerk-prisma
// Reçoit et vérifie les events Clerk via Svix.
// Personnaliser les handlers ci-dessous pour synchroniser avec votre base de données.
// Requiert : WEBHOOK_SECRET dans .env.local (clé Svix depuis Clerk Dashboard)
export const dynamic = 'force-dynamic'
import { NextRequest, NextResponse } from 'next/server'
import { Webhook } from 'svix'

type ClerkEvent = {
  type: string
  data: Record<string, unknown>
}

export async function POST(req: NextRequest) {
  const secret = process.env.WEBHOOK_SECRET
  if (!secret) {
    console.error('[clerk-webhook] WEBHOOK_SECRET manquant dans .env.local')
    return NextResponse.json({ error: 'Configuration error' }, { status: 500 })
  }

  const svix_id = req.headers.get('svix-id')
  const svix_timestamp = req.headers.get('svix-timestamp')
  const svix_signature = req.headers.get('svix-signature')

  if (!svix_id || !svix_timestamp || !svix_signature) {
    return NextResponse.json({ error: 'Missing svix headers' }, { status: 400 })
  }

  const body = await req.text()
  const wh = new Webhook(secret)

  let event: ClerkEvent
  try {
    event = wh.verify(body, {
      'svix-id': svix_id,
      'svix-timestamp': svix_timestamp,
      'svix-signature': svix_signature,
    }) as ClerkEvent
  } catch {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  // Personnaliser ici pour synchroniser les événements Clerk avec votre base de données.
  // Si votre schema.prisma a un modèle User, décommentez et adaptez :
  //
  // import prisma from '@/lib/prisma'
  // if (event.type === 'user.created') {
  //   const d = event.data as { id: string; email_addresses: Array<{ email_address: string }> }
  //   await prisma.user.create({ data: { id: d.id, email: d.email_addresses[0]?.email_address ?? '' } })
  // }

  console.log('[clerk-webhook] Event reçu :', event.type)
  return NextResponse.json({ received: true })
}
