import handler from '../../../src/pages/api/users';
import { createMocks } from 'node-mocks-http';
import { getAuth } from '@clerk/nextjs/api';

jest.mock('@clerk/nextjs/api', () => ({
  getAuth: jest.fn(),
}));

describe('/api/users API Endpoint', () => {
  it('should return 401 if user is not authenticated', async () => {
    (getAuth as jest.Mock).mockReturnValue({ userId: null });
    const { req, res } = createMocks({ method: 'GET' });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(401);
    expect(res._getJSONData()).toEqual({ message: 'Unauthorized' });
  });

  it('should allow authenticated user to access', async () => {
    (getAuth as jest.Mock).mockReturnValue({ userId: 'user_123' });
    const { req, res } = createMocks({ method: 'GET' });

    await handler(req, res);

    expect(res._getStatusCode()).not.toBe(401);
  });

  it('should return 405 for unsupported methods', async () => {
    (getAuth as jest.Mock).mockReturnValue({ userId: 'user_123' });
    const { req, res } = createMocks({ method: 'PATCH' });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(405);
    expect(res._getHeaders().allow).toEqual(['GET', 'POST', 'PUT', 'DELETE']);
  });
});
