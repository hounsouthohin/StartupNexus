import { clerkMiddleware } from '@clerk/nextjs/server';
import middleware from '../middleware';

jest.mock('@clerk/nextjs/server', () => ({
  clerkMiddleware: jest.fn((handler) => handler),
  createRouteMatcher: jest.fn(() => jest.fn(() => true)),
}));

describe('middleware', () => {
  it('calls clerkMiddleware with the correct handler', () => {
    const handler = jest.fn();
    middleware(handler);
    expect(clerkMiddleware).toHaveBeenCalledWith(expect.any(Function));
  });
});
