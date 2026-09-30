import Link from 'next/link'

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 text-center">
      <h1 className="text-4xl font-bold text-foreground mb-4">Abo Tracker</h1>
      <p className="text-muted-foreground mb-8 max-w-md">Connectez-vous pour accéder à votre espace.</p>
      <Link href="/sign-in" className="px-6 py-3 bg-primary text-white rounded-md font-medium hover:bg-primary/85">Se connecter</Link>
    </main>
  )
}
