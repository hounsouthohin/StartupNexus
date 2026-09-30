"use client"
import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { UserButton } from "@clerk/nextjs"

interface NavItem { href: string; label: string; exact?: boolean; priv?: boolean; base?: boolean }

// Rôle privilégié (vide = mono-acteur). Nav filtrée par la SURFACE de l'acteur (S2).
// Annoté `string` : sinon TS réduit au littéral et `!== ""` = comparaison sans overlap (TS2367).
const PRIVILEGED_ROLE: string = ""

const NAV: NavItem[] = [
  { href: "/dashboard", label: "Tableau de bord", exact: true, priv: true, base: true },
  { href: "/dashboard/categories", label: "Catégories", exact: false, priv: true, base: true },
  { href: "/dashboard/subscriptions", label: "Abonnements", exact: false, priv: true, base: true },
]

export function DashboardShell({ children, role }: { children: React.ReactNode; role?: string | null }) {
  const pathname = usePathname()
  const PUBLIC_PATHS: string[] = ["/"]
  const isAuthPage = pathname.startsWith("/sign-in") || pathname.startsWith("/sign-up") || PUBLIC_PATHS.some(p => pathname === p || pathname.startsWith(p + "/"))

  if (isAuthPage) return <>{children}</>

  const isPrivileged = PRIVILEGED_ROLE !== "" && role === PRIVILEGED_ROLE
  const navItems = NAV.filter((i) => (isPrivileged ? i.priv !== false : i.base !== false))

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <aside className="w-60 shrink-0 bg-white border-r border-gray-200 flex flex-col">
        <div className="h-14 flex items-center px-5 border-b border-gray-200">
          <span className="text-base font-semibold text-gray-900 truncate">Mon Suivi d'Abonnements</span>
        </div>
        <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => {
            const active = item.exact
              ? pathname === item.href
              : pathname === item.href || pathname.startsWith(item.href + "/")
            return (
              <Link
                key={item.href}
                href={item.href}
                className={[
                  "flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-150",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
                ].join(" ")}
              >
                {item.label}
              </Link>
            )
          })}
        </nav>
        <div className="p-3 border-t border-gray-200">
          <UserButton />
        </div>
      </aside>
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
