import { notFound } from "next/navigation";
import prisma from "@/lib/prisma";

export const dynamic = "force-dynamic";

type BlogPageProps = {
  params: {
    slug: string;
  };
};

export default async function BlogPostPage({ params }: BlogPageProps) {
  try {
    const post = await prisma.post.findUnique({
      where: { slug: params.slug },
      select: {
        title: true,
        content: true,
        published: true,
      },
    });

    if (!post || !post.published) {
      notFound();
    }

    return (
      <main className="mx-auto max-w-3xl p-6">
        <h1 className="mb-4 text-3xl font-bold">{post.title}</h1>
        <article className="prose max-w-none whitespace-pre-wrap">
          {post.content}
        </article>
      </main>
    );
  } catch {
    notFound();
  }
}
