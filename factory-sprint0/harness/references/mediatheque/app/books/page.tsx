import BooksClient from './page-client'
import { bookService } from '@/lib/services/book.service'

export const dynamic = 'force-dynamic'

export default async function BooksPage() {
  const items = await bookService.getPublicAll()
  return <BooksClient items={items} />
}
