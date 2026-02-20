import { Clerk } from '@clerk/nextjs';
import { z } from 'zod';

const profileSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
  profilePicture: z.string().url().optional(),
});

export default async function handler(req, res) {
  const { method } = req;

  if (method === 'GET') {
    const user = Clerk.getUser(req);
    return res.status(200).json(user);
  } else if (method === 'PUT') {
    const parsedData = profileSchema.safeParse(req.body);
    if (!parsedData.success) {
      return res.status(400).json(parsedData.error);
    }
    // Update user profile logic here
    return res.status(200).json({ message: 'Profile updated' });
  }
  return res.status(405).json({ message: 'Method not allowed' });
}