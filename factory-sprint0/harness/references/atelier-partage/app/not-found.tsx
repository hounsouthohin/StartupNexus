import Link from 'next/link'

export default function NotFound() {
  return (
    <main className="container mx-auto p-6 text-center">
      <h2 className="text-2xl font-semibold mb-4">Page introuvable</h2>
      <p className="text-gray-500 mb-6">
        La ressource demandée n'existe pas ou a été supprimée.
      </p>
      <Link href="/" className="text-blue-600 hover:underline">
        Retour à l'accueil
      </Link>
    </main>
  )
}
