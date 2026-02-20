import handler from '../../../app/api/posts';
import { createMocks } from 'node-mocks-http';
import { getSession } from '@clerk/nextjs/api';

jest.mock('@clerk/nextjs/api', () => ({
  getSession: jest.fn(),
}));

describe('/api/posts', () => {
  it('returns 401 if no session', async () => {
    (getSession as jest.Mock).mockResolvedValue(null);
    const { req, res } = createMocks({ method: 'GET' });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(401);
    expect(res._getJSONData()).toEqual({ error: 'Unauthorized' });
  });

  it('returns posts on GET if session exists', async () => {
    (getSession as jest.Mock).mockResolvedValue({ user: { id: 'user_123' } });
    const { req, res } = createMocks({ method: 'GET' });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(200);
    expect(res._getJSONData()).toEqual({ posts: [] });
  });

  it('creates a post on POST if session exists', async () => {
    (getSession as jest.Mock).mockResolvedValue({ user: { id: 'user_123' } });
    const { req, res } = createMocks({
      method: 'POST',
      body: { title: 'New Post', content: 'Content of the post' },
    });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(201);
    expect(res._getJSONData()).toEqual({ message: 'Post created', data: { title: 'New Post', content: 'Content of the post' } });
  });

  it('returns 400 on POST with invalid data', async () => {
    (getSession as jest.Mock).mockResolvedValue({ user: { id: 'user_123' } });
    const { req, res } = createMocks({
      method: 'POST',
      body: { title: 'New Post', content: 123 },
    });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(400);
    expect(res._getJSONData()).toHaveProperty('error');
  });
});
