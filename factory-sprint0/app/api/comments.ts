import { NextApiRequest, NextApiResponse } from 'next';
import { getSession } from '@clerk/nextjs/api';
import { z } from 'zod';

const commentSchema = z.object({
  postId: z.string(),
  content: z.string(),
});

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const session = await getSession(req);

  if (!session) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  switch (req.method) {
    case 'GET':
      // Logic to retrieve comments
      return res.status(200).json({ comments: [] }); // Placeholder
    case 'POST':
      try {
        const parsedData = commentSchema.parse(req.body);
        // Logic to create a new comment
        return res.status(201).json({ message: 'Comment created', data: parsedData });
      } catch (error) {
        return res.status(400).json({ error: error.errors });
      }
    default:
      return res.status(405).json({ error: 'Method Not Allowed' });
  }
}