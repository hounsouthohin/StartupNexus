import Link from 'next/link'

export default function Navigation() {
  return (
    <nav className="flex items-center gap-6">
      <Link href="/" className="text-sm text-gray-600 hover:text-gray-900 font-medium">Home</Link>
      <Link href="/leave-requests" className="text-sm text-gray-600 hover:text-gray-900 font-medium">Leave Requests</Link>
    </nav>
  )
}
