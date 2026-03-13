import Link from "next/link";
import prisma from "@/lib/prisma";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let posts: Array<{ id: string; title: string; slug: string; createdAt: Date }> = [];
  try {
    posts = await prisma.post.findMany({
      where: { published: true },
      orderBy: { createdAt: "desc" },
      select: {
        id: true,
        title: true,
        slug: true,
        createdAt: true,
      },
    });
  } catch {
    posts = [];
  }

  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="mb-4 text-2xl font-bold">Blog</h1>
      {posts.length === 0 ? (
        <p className="text-sm text-gray-600">Aucun article publie.</p>
      ) : (
        <ul className="space-y-3">
          {posts.map((post) => (
            <li key={post.id} className="rounded border p-4">
              <Link className="text-lg font-semibold hover:underline" href={`/blog/${post.slug}`}>
                {post.title}
              </Link>
              <p className="mt-1 text-xs text-gray-500">
                {new Date(post.createdAt).toLocaleDateString()}
              </p>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
