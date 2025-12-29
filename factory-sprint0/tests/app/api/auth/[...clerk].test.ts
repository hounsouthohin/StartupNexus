import { auth } from '@clerk/nextjs/api';

jest.mock('@clerk/nextjs/api', () => ({
  auth: jest.fn(() => jest.fn()),
}));

describe('auth API route', () => {
  it('should export auth function', () => {
    const authFunction = require('../../../app/api/auth/[...clerk]').default;
    expect(auth).toHaveBeenCalled();
    expect(typeof authFunction).toBe('function');
  });
});
