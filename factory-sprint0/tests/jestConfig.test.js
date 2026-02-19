// jest.config.js is a configuration file, so we don't typically write unit tests for it.
// However, we can write a test to ensure that the Jest configuration is correctly set up.

describe('jest.config.js', () => {
  it('should have the correct test environment', () => {
    const jestConfig = require('../jest.config.js');
    expect(jestConfig.testEnvironment).toBe('jsdom');
  });

  it('should ignore the correct paths', () => {
    const jestConfig = require('../jest.config.js');
    expect(jestConfig.testPathIgnorePatterns).toEqual(['/node_modules/', '/.next/']);
  });

  it('should have the correct transform configuration', () => {
    const jestConfig = require('../jest.config.js');
    expect(jestConfig.transform['^.+\.(js|jsx|ts|tsx)$']).toEqual(['babel-jest', { presets: ['next/babel'] }]);
  });

  it('should map modules correctly', () => {
    const jestConfig = require('../jest.config.js');
    expect(jestConfig.moduleNameMapper['^@/(.*)$']).toBe('<rootDir>/src/$1');
    expect(jestConfig.moduleNameMapper['\.css$']).toBe('identity-obj-proxy');
  });
});
