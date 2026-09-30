"use client"
import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { UserButton, useUser } from "@clerk/nextjs"

interface NavItem { href: string; label: string; exact?: boolean; priv?: boolean; base?: boolean }

// Rôle privilégié (vide = mono-acteur). Les liens sont filtrés par la SURFACE de l'acteur (S2) :
// chacun ne voit dans sa nav que ce qui compose SON app. Annoté `string` (sinon TS réduit au
// type littéral et `!== ""` devient une comparaison « sans overlap » → TS2367).
const PRIVILEGED_ROLE: string = "librarian"

const AUTH_NAV: NavItem[] = [
  { href: "/dashboard", label: "Tableau de bord", exact: true, priv: true, base: true },
  { href: "/dashboard/borrowings", label: "Emprunts", exact: false, priv: true, base: true },
  { href: "/dashboard/profile", label: "Adhérents", exact: false, priv: false, base: true },
]

const PUBLIC_NAV: NavItem[] = [
  { href: "/", label: "Accueil", exact: true, priv: true, base: true },
  { href: "/books", label: "Ouvrages", exact: false, priv: true, base: true },
]

export function TopNavShell({ children, role }: { children: React.ReactNode; role?: string | null }) {
  const pathname = usePathname()
  const { isSignedIn } = useUser()
  const isAuthPage = pathname.startsWith("/sign-in") || pathname.startsWith("/sign-up")

  if (isAuthPage) return <>{children}</>

  const isPrivileged = PRIVILEGED_ROLE !== "" && role === PRIVILEGED_ROLE
  const authNav = AUTH_NAV.filter((i) => (isPrivileged ? i.priv !== false : i.base !== false))
  const nav = isSignedIn ? authNav : PUBLIC_NAV

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <span className="text-base font-semibold text-foreground">Mediatheque</span>
            <nav className="hidden md:flex items-center gap-1">
              {nav.map((item) => {
                const active = item.exact
                  ? pathname === item.href
                  : pathname === item.href || pathname.startsWith(item.href + "/")
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={[
                      "px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-300 ease-out",
                      active
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
                    ].join(" ")}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </nav>
          </div>
          <div className="flex items-center gap-2">
            {!isSignedIn && (
              <Link
                href="/sign-in"
                className="px-4 py-1.5 rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-300 ease-out"
              >
                Connexion
              </Link>
            )}
            <UserButton />
          </div>
        </div>
      </header>
      <main>{children}</main>
    </div>
  )
}
