import { ClerkProvider } from "@clerk/nextjs"
import { TopNavShell } from "@/app/components/layout/TopNavShell"
import "./globals.css"
import type { ReactNode } from "react"

export const metadata = { title: "Club Running" }

export default function RootLayout({ children }: { children: ReactNode }) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  const canUseClerk =
    typeof publishableKey === "string" &&
    publishableKey.startsWith("pk_") &&
    !publishableKey.includes("placeholder")

  if (!canUseClerk) {
    return (
      <html lang="fr">
        <body>{children}</body>
      </html>
    )
  }

  return (
    <ClerkProvider publishableKey={publishableKey}>
      <html lang="fr">
        <body>
          <TopNavShell>{children}</TopNavShell>
        </body>
      </html>
    </ClerkProvider>
  )
}
