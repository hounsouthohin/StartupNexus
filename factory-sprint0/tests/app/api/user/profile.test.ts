import handler from '../../../app/api/user/profile.ts';
import { createMocks } from 'node-mocks-http';
import { Clerk } from '@clerk/nextjs';

jest.mock('@clerk/nextjs', () => ({
  Clerk: {
    getUser: jest.fn().mockReturnValue({ id: 'user_123', name: 'John Doe' }),
  },
}));

describe('/api/user/profile API Endpoint', () => {
  it('should return user data on GET', async () => {
    const { req, res } = createMocks({ method: 'GET' });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(200);
    expect(JSON.parse(res._getData())).toEqual({ id: 'user_123', name: 'John Doe' });
  });

  it('should update user profile on PUT', async () => {
    const { req, res } = createMocks({
      method: 'PUT',
      body: { name: 'Jane Doe', email: 'jane.doe@example.com' },
    });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(200);
    expect(JSON.parse(res._getData())).toEqual({ message: 'Profile updated' });
  });

  it('should return 400 on invalid PUT data', async () => {
    const { req, res } = createMocks({
      method: 'PUT',
      body: { email: 'not-an-email' },
    });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(400);
  });

  it('should return 405 on unsupported method', async () => {
    const { req, res } = createMocks({ method: 'POST' });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(405);
  });
});
