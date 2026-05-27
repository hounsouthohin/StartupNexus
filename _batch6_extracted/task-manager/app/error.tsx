'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <main className="container mx-auto p-6 text-center">
      <h2 className="text-xl font-semibold text-red-600 mb-4">
        Une erreur est survenue
      </h2>
      <p className="text-gray-500 mb-6">{error.message}</p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Réessayer
      </button>
    </main>
  )
}
