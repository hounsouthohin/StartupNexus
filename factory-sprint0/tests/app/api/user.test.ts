import handler from '../../../app/api/user';
import { createMocks } from 'node-mocks-http';
import { getSession } from '@clerk/nextjs/api';

jest.mock('@clerk/nextjs/api', () => ({
  getSession: jest.fn(),
}));

describe('/api/user', () => {
  it('returns 401 if no session', async () => {
    (getSession as jest.Mock).mockResolvedValue(null);
    const { req, res } = createMocks({ method: 'GET' });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(401);
    expect(res._getJSONData()).toEqual({ error: 'Unauthorized' });
  });

  it('returns user data on GET if session exists', async () => {
    const mockUser = { id: 'user_123', email: 'test@example.com' };
    (getSession as jest.Mock).mockResolvedValue({ user: mockUser });
    const { req, res } = createMocks({ method: 'GET' });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(200);
    expect(res._getJSONData()).toEqual({ user: mockUser });
  });

  it('updates user data on PUT if session exists', async () => {
    (getSession as jest.Mock).mockResolvedValue({ user: { id: 'user_123' } });
    const { req, res } = createMocks({
      method: 'PUT',
      body: { name: 'New Name' },
    });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(200);
    expect(res._getJSONData()).toEqual({ message: 'Profile updated', data: { name: 'New Name' } });
  });

  it('returns 400 on PUT with invalid data', async () => {
    (getSession as jest.Mock).mockResolvedValue({ user: { id: 'user_123' } });
    const { req, res } = createMocks({
      method: 'PUT',
      body: { name: 123 },
    });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(400);
    expect(res._getJSONData()).toHaveProperty('error');
  });
});
