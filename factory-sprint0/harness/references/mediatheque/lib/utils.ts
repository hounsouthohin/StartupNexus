import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Formatage déterministe d'une date (ISO ou Date) en français lisible.
// Une seule réponse correcte → déterministe. Renvoie "" pour une valeur vide/invalide.
export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return ""
  const d = value instanceof Date ? value : new Date(value)
  if (isNaN(d.getTime())) return ""
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" })
}

// Formatage déterministe d'un montant en euros (ex: 12.99 → "12,99 €").
// Piloté par l'annotation "currency" de l'architect. Renvoie "" si valeur invalide.
export function formatCurrency(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") return ""
  const n = typeof value === "number" ? value : Number(value)
  if (isNaN(n)) return ""
  return n.toLocaleString("fr-FR", { style: "currency", currency: "EUR" })
}
