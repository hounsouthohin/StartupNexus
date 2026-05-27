import BlogClient from './page-client'
import { postService } from '@/lib/services/post.service'

export const dynamic = 'force-dynamic'

export default async function BlogPage() {
  const items = await postService.getPublicAll()
  return <BlogClient items={items} />
}
