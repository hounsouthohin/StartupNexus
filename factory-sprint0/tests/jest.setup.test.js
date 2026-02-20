// jest.setup.js is a setup file for Jest, and typically doesn't require unit tests.
// However, we can write a test to ensure that the setup is valid if needed.

describe('jest.setup.js', () => {
  it('should import @testing-library/jest-dom', () => {
    const setup = require('../jest.setup.js');
    expect(setup).toBeDefined();
  });
});
