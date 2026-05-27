import { notFound } from 'next/navigation'
import BlogIdClient from './page-client'
import { postService } from '@/lib/services/post.service'

export const dynamic = 'force-dynamic'

export default async function BlogIdPage({ params }: { params: { id: string } }) {
  const item = await postService.getPublicByIdWithRelations(params.id)
  if (!item) notFound()
  return <BlogIdClient item={item} />
}
