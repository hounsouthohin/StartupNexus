import { POST } from '../../../app/api/user/route';
import { NextResponse } from 'next/server';

jest.mock('next/server', () => ({
  NextResponse: {
    json: jest.fn((body, init) => ({ body, ...init })),
  },
}));

describe('POST /api/user', () => {
  it('should return 400 if validation fails', async () => {
    const request = {
      json: async () => ({ email: 'invalid-email', password: 'short' }),
    };
    const response = await POST(request);
    expect(NextResponse.json).toHaveBeenCalledWith({
      error: expect.any(Array),
    }, { status: 400 });
  });

  it('should return 201 if validation succeeds', async () => {
    const request = {
      json: async () => ({ email: 'test@example.com', password: 'validpassword' }),
    };
    const response = await POST(request);
    expect(NextResponse.json).toHaveBeenCalledWith({
      message: 'User created successfully',
    }, { status: 201 });
  });
});
