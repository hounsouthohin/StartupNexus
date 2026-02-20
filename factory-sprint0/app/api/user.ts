import { NextApiRequest, NextApiResponse } from 'next';
import { getSession } from '@clerk/nextjs/api';
import { z } from 'zod';

const userSchema = z.object({
  name: z.string().optional(),
});

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const session = await getSession(req);

  if (!session) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  switch (req.method) {
    case 'GET':
      // Logic to retrieve user profile information
      return res.status(200).json({ user: session.user });
    case 'PUT':
      try {
        const parsedData = userSchema.parse(req.body);
        // Logic to update user profile information
        return res.status(200).json({ message: 'Profile updated', data: parsedData });
      } catch (error) {
        return res.status(400).json({ error: error.errors });
      }
    default:
      return res.status(405).json({ error: 'Method Not Allowed' });
  }
}