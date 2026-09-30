"use client"
import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { UserButton } from "@clerk/nextjs"

interface NavItem { href: string; label: string; exact?: boolean; priv?: boolean; base?: boolean }

// Rôle privilégié (vide = mono-acteur). Nav filtrée par la SURFACE de l'acteur (S2).
// Annoté `string` : sinon TS réduit au littéral et `!== ""` = comparaison sans overlap (TS2367).
const PRIVILEGED_ROLE: string = "admin"

const NAV: NavItem[] = [
  { href: "/requests", label: "Demandes", exact: false, priv: true, base: true },
]

export function DashboardShell({ children, role }: { children: React.ReactNode; role?: string | null }) {
  const pathname = usePathname()
  const PUBLIC_PATHS: string[] = ["/"]
  const isAuthPage = pathname.startsWith("/sign-in") || pathname.startsWith("/sign-up") || PUBLIC_PATHS.some(p => pathname === p || pathname.startsWith(p + "/"))

  if (isAuthPage) return <>{children}</>

  const isPrivileged = PRIVILEGED_ROLE !== "" && role === PRIVILEGED_ROLE
  const navItems = NAV.filter((i) => (isPrivileged ? i.priv !== false : i.base !== false))

  return (
    <div className="flex h-screen overflow-hidden bg-gray-100">
      <aside className="w-60 shrink-0 bg-indigo-900 border-r border-slate-700 flex flex-col">
        <div className="h-14 flex items-center px-5 border-b border-slate-700">
          <span className="text-base font-semibold text-white truncate">IT Request Manager</span>
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
                    ? "bg-primary text-primary-foreground"
                    : "text-slate-300 hover:bg-slate-700 hover:text-white",
                ].join(" ")}
              >
                {item.label}
              </Link>
            )
          })}
        </nav>
        <div className="p-3 border-t border-slate-700">
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
