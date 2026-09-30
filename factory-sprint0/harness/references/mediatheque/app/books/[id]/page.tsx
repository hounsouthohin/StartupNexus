import { notFound } from 'next/navigation'
import BooksIdClient from './page-client'
import { bookService } from '@/lib/services/book.service'

export const dynamic = 'force-dynamic'

export default async function BooksIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const item = await bookService.getPublicById(id)
  if (!item) notFound()
  return <BooksIdClient item={item} />
}
