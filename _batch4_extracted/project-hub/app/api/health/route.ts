export const dynamic = 'force-dynamic'

import { NextResponse } from 'next/server'
import prisma from '@/lib/prisma'

export async function GET() {
  try {
    await Promise.race([
      prisma.$queryRaw`SELECT 1`,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('DB timeout')), 3000)
      ),
    ])
    return NextResponse.json({ status: 'ok', db: 'ok' })
  } catch {
    return NextResponse.json({ status: 'degraded', db: 'unreachable' }, { status: 503 })
  }
}
