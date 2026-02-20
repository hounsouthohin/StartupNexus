describe('jest.config.js', () => {
  it('should have correct test environment', () => {
    const jestConfig = require('../../jest.config.js');
    expect(jestConfig.testEnvironment).toBe('jsdom');
  });

  it('should setup files after env', () => {
    const jestConfig = require('../../jest.config.js');
    expect(jestConfig.setupFilesAfterEnv).toEqual(['<rootDir>/jest.setup.js']);
  });

  it('should ignore correct test paths', () => {
    const jestConfig = require('../../jest.config.js');
    expect(jestConfig.testPathIgnorePatterns).toEqual(['/node_modules/', '/.next/']);
  });

  it('should have correct transform configuration', () => {
    const jestConfig = require('../../jest.config.js');
    expect(jestConfig.transform).toEqual({
      '^.+\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }],
    });
  });

  it('should have correct module name mapper', () => {
    const jestConfig = require('../../jest.config.js');
    expect(jestConfig.moduleNameMapper).toEqual({
      '^@/(.*)$': '<rootDir>/src/$1',
      '\.(css)$': 'identity-obj-proxy',
    });
  });
});
