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
