// AUTO-GÉNÉRÉ PAR factory stack nextjs-clerk-prisma — NE PAS MODIFIER
// Synchronise les événements Clerk (user.created / user.updated / user.deleted)
// avec la table User de la base de données Prisma.
// Requiert : WEBHOOK_SECRET dans .env.local (clé Svix depuis Clerk Dashboard)
export const dynamic = 'force-dynamic'
import { NextRequest, NextResponse } from 'next/server'
import { Webhook } from 'svix'
import prisma from '@/lib/prisma'

type ClerkUserEvent = {
  type: string
  data: {
    id: string
    email_addresses: Array<{ email_address: string; id: string }>
    primary_email_address_id: string
    first_name: string | null
    last_name: string | null
  }
}

export async function POST(req: NextRequest) {
  const secret = process.env.WEBHOOK_SECRET
  if (!secret) {
    console.error('[clerk-webhook] WEBHOOK_SECRET manquant dans .env.local')
    return NextResponse.json({ error: 'Configuration error' }, { status: 500 })
  }

  // Vérification de la signature Svix
  const svix_id = req.headers.get('svix-id')
  const svix_timestamp = req.headers.get('svix-timestamp')
  const svix_signature = req.headers.get('svix-signature')

  if (!svix_id || !svix_timestamp || !svix_signature) {
    return NextResponse.json({ error: 'Missing svix headers' }, { status: 400 })
  }

  const body = await req.text()
  const wh = new Webhook(secret)

  let event: ClerkUserEvent
  try {
    event = wh.verify(body, {
      'svix-id': svix_id,
      'svix-timestamp': svix_timestamp,
      'svix-signature': svix_signature,
    }) as ClerkUserEvent
  } catch {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  const { type, data } = event
  const primaryEmail = data.email_addresses.find(
    (e) => e.id === data.primary_email_address_id,
  )?.email_address ?? ''

  const name = [data.first_name, data.last_name].filter(Boolean).join(' ') || null

  try {
    if (type === 'user.created') {
      await prisma.user.create({
        data: { id: data.id, email: primaryEmail, name },
      })
    } else if (type === 'user.updated') {
      await prisma.user.upsert({
        where: { id: data.id },
        update: { email: primaryEmail, name },
        create: { id: data.id, email: primaryEmail, name },
      })
    } else if (type === 'user.deleted') {
      await prisma.user.delete({ where: { id: data.id } }).catch(() => null)
    }
  } catch (err) {
    console.error('[clerk-webhook] Erreur DB :', err)
    return NextResponse.json({ error: 'Database error' }, { status: 500 })
  }

  return NextResponse.json({ received: true })
}
