import { withClerkMiddleware } from '@clerk/nextjs/middleware';
import middleware from '../../middleware';

jest.mock('@clerk/nextjs/middleware', () => ({
  withClerkMiddleware: jest.fn((handler) => handler),
}));

describe('middleware', () => {
  it('should call withClerkMiddleware', () => {
    expect(withClerkMiddleware).toHaveBeenCalledWith(expect.any(Function));
  });
});
