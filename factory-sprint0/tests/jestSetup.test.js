// jest.setup.js is a setup file for Jest, so we don't typically write unit tests for it.
// However, we can write a test to ensure that the Jest setup is correctly configured.

describe('jest.setup.js', () => {
  it('should import @testing-library/jest-dom', () => {
    const jestSetup = require('../jest.setup.js');
    expect(jestSetup).toBeDefined();
  });
});
