import handler from '../../../app/api/auth';
import { createMocks } from 'node-mocks-http';
import { getAuth } from '@clerk/nextjs/api';

jest.mock('@clerk/nextjs/api', () => ({
  getAuth: jest.fn(),
}));

describe('/api/auth', () => {
  it('returns 401 if no userId', async () => {
    (getAuth as jest.Mock).mockReturnValue({ userId: null });
    const { req, res } = createMocks({ method: 'GET' });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(401);
    expect(res._getJSONData()).toEqual({ error: 'Unauthorized' });
  });

  it('returns userId if authenticated', async () => {
    (getAuth as jest.Mock).mockReturnValue({ userId: 'user_123' });
    const { req, res } = createMocks({ method: 'GET' });

    await handler(req, res);

    expect(res._getStatusCode()).toBe(200);
    expect(res._getJSONData()).toEqual({ userId: 'user_123' });
  });
});
