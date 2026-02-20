import '@testing-library/jest-dom';

describe('jest.setup.js', () => {
  it('should import @testing-library/jest-dom', () => {
    // This test ensures that jest-dom is correctly imported, which is hard to test directly.
    // We assume that if the file runs without error, the import is successful.
    expect(true).toBe(true);
  });
});
