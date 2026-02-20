import handler from '../../../app/api/data.ts';
import { createMocks } from 'node-mocks-http';

describe('/api/data API Endpoint', () => {
  it('should retrieve data on GET', async () => {
    const { req, res } = createMocks({ method: 'GET' });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(200);
    expect(JSON.parse(res._getData())).toEqual({ message: 'Data retrieved' });
  });

  it('should create data on POST with valid data', async () => {
    const { req, res } = createMocks({
      method: 'POST',
      body: { title: 'New Data' },
    });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(201);
    expect(JSON.parse(res._getData())).toEqual({ message: 'Data created' });
  });

  it('should return 400 on POST with invalid data', async () => {
    const { req, res } = createMocks({
      method: 'POST',
      body: { title: 123 },
    });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(400);
  });

  it('should return 405 on unsupported method', async () => {
    const { req, res } = createMocks({ method: 'DELETE' });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(405);
  });
});
