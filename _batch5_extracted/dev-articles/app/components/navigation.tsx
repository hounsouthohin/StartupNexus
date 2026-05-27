import Link from 'next/link'

export default function Navigation() {
  return (
    <nav className="flex items-center gap-6">
      <Link href="/" className="text-sm text-gray-600 hover:text-gray-900 font-medium">Home</Link>
      <Link href="/articles" className="text-sm text-gray-600 hover:text-gray-900 font-medium">Articles</Link>
      <Link href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900 font-medium">Dashboard</Link>
    </nav>
  )
}
