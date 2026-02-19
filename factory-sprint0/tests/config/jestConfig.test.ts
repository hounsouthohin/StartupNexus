// Jest configuration is typically not unit tested, but we can validate its structure.

describe('jest.config.js', () => {
  it('should have the correct test environment and setup files', () => {
    const jestConfig = require('../../jest.config.js');
    expect(jestConfig.testEnvironment).toBe('jsdom');
    expect(jestConfig.setupFilesAfterEnv).toContain('<rootDir>/jest.setup.js');
  });

  it('should ignore the correct paths', () => {
    const jestConfig = require('../../jest.config.js');
    expect(jestConfig.testPathIgnorePatterns).toContain('/node_modules/');
    expect(jestConfig.testPathIgnorePatterns).toContain('/.next/');
  });

  it('should have the correct transform configuration', () => {
    const jestConfig = require('../../jest.config.js');
    expect(jestConfig.transform['^.+\.(js|jsx|ts|tsx)$']).toEqual(['babel-jest', { presets: ['next/babel'] }]);
  });

  it('should have the correct module name mapper', () => {
    const jestConfig = require('../../jest.config.js');
    expect(jestConfig.moduleNameMapper['^@/(.*)$']).toBe('<rootDir>/src/$1');
    expect(jestConfig.moduleNameMapper['\.css$']).toBe('identity-obj-proxy');
  });
});
