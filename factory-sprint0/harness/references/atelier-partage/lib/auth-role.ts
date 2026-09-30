// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
import { auth, clerkClient } from '@clerk/nextjs/server'

const PRIVILEGED_ROLE = 'animator'
// Emails désignés admin par l'opérateur (bootstrap), séparés par des virgules.
const ADMIN_EMAILS = (process.env.ADMIN_EMAILS ?? '')
  .split(',').map((s) => s.trim().toLowerCase()).filter(Boolean)

/** Rôle applicatif de l'utilisateur courant. Porte 1 : email bootstrap. Porte 2 : fiche Clerk. */
export async function getCurrentRole(): Promise<string | null> {
  const { userId } = await auth()
  if (!userId) return null
  const client = await clerkClient()
  const user = await client.users.getUser(userId)
  if (ADMIN_EMAILS.length > 0) {
    const emails = user.emailAddresses.map((e) => e.emailAddress.toLowerCase())
    if (emails.some((e) => ADMIN_EMAILS.includes(e))) return PRIVILEGED_ROLE
  }
  const role = (user.publicMetadata as { role?: string } | null)?.role
  return typeof role === 'string' ? role : null
}

/** True si l'utilisateur courant détient le rôle attendu. */
export async function hasRole(role: string): Promise<boolean> {
  return (await getCurrentRole()) === role
}

/** Lève une erreur si l'utilisateur n'a pas le rôle requis — garde d'action serveur. */
export async function requireRole(role: string): Promise<void> {
  if (!(await hasRole(role))) {
    throw new Error("Action réservée : vous n'avez pas les droits nécessaires.")
  }
}
