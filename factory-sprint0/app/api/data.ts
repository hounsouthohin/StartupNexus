import { z } from 'zod';

const dataSchema = z.object({
  title: z.string(),
  description: z.string().optional(),
});

export default async function handler(req, res) {
  const { method } = req;

  if (method === 'GET') {
    // Retrieve application-specific data logic here
    return res.status(200).json({ message: 'Data retrieved' });
  } else if (method === 'POST') {
    const parsedData = dataSchema.safeParse(req.body);
    if (!parsedData.success) {
      return res.status(400).json(parsedData.error);
    }
    // Create new data entry logic here
    return res.status(201).json({ message: 'Data created' });
  }
  return res.status(405).json({ message: 'Method not allowed' });
}