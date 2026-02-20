import { formatDate } from '../../../app/utils/helpers';

describe('formatDate', () => {
  it('formats a date correctly', () => {
    const date = new Date('2023-01-01T00:00:00Z');
    expect(formatDate(date)).toBe('1/1/2023');
  });
});
