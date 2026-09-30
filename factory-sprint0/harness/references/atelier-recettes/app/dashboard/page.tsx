import Link from 'next/link'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { recipeService } from '@/lib/services/recipe.service'
import { tagService } from '@/lib/services/tag.service'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const recipes = await recipeService.getAll(userId, 1, 100000)
  const tags = await tagService.getAll(userId, 1, 100000)

  const kpi0 = recipes.length
  const kpi1 = tags.length

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Total des recettes</p>
          <p className="text-3xl font-bold text-foreground">{kpi0}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Total des tags</p>
          <p className="text-3xl font-bold text-foreground">{kpi1}</p>
        </div>
      </div>
      
      <div className="flex flex-wrap gap-3">
        <Link href="/dashboard/recipes" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Recettes</Link>
        <Link href="/dashboard/tags" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Tags</Link>
      </div>
    </main>
  )
}
