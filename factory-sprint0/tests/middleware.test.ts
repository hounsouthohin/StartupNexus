import middleware from '../middleware';
import { withClerkMiddleware } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

jest.mock('@clerk/nextjs/server', () => ({
  withClerkMiddleware: jest.fn((handler) => handler),
}));

jest.mock('next/server', () => ({
  NextResponse: {
    next: jest.fn(),
  },
}));

describe('middleware', () => {
  it('should call NextResponse.next()', () => {
    const req = {};
    const res = {};
    middleware(req, res);
    expect(NextResponse.next).toHaveBeenCalled();
  });
});
