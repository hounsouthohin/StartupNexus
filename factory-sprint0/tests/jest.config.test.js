// jest.config.js is a configuration file for Jest, and typically doesn't require unit tests.
// However, we can write a test to ensure that the configuration is valid if needed.

describe('jest.config.js', () => {
  it('should have a valid Jest configuration', () => {
    const config = require('../jest.config.js');
    expect(config.testEnvironment).toBe('jsdom');
    expect(config.setupFilesAfterEnv).toContain('<rootDir>/jest.setup.js');
    expect(config.testPathIgnorePatterns).toContain('/node_modules/');
  });
});
