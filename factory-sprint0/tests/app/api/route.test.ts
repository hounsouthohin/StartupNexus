import { GET } from '../../../app/api/route.ts';
import { NextResponse } from 'next/server';

jest.mock('next/server', () => ({
  NextResponse: {
    json: jest.fn((data) => data),
  },
}));

describe('API Route', () => {
  it('returns a JSON response with a message', async () => {
    const request = new Request('http://localhost/api');
    const response = await GET(request);
    expect(NextResponse.json).toHaveBeenCalledWith({ message: 'Hello from API!' });
    expect(response).toEqual({ message: 'Hello from API!' });
  });
});
