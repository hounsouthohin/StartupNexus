import handler from '../../../../app/api/data/[id].ts';
import { createMocks } from 'node-mocks-http';

describe('/api/data/[id] API Endpoint', () => {
  it('should update data on PUT', async () => {
    const { req, res } = createMocks({ method: 'PUT' });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(200);
    expect(JSON.parse(res._getData())).toEqual({ message: 'Data updated' });
  });

  it('should delete data on DELETE', async () => {
    const { req, res } = createMocks({ method: 'DELETE' });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(200);
    expect(JSON.parse(res._getData())).toEqual({ message: 'Data deleted' });
  });

  it('should return 405 on unsupported method', async () => {
    const { req, res } = createMocks({ method: 'POST' });
    await handler(req, res);
    expect(res._getStatusCode()).toBe(405);
  });
});
