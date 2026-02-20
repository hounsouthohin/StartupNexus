// Since tsconfig.json is a configuration file for TypeScript, it doesn't require unit tests.
// However, we can write a test to ensure that the configuration is valid if needed.

describe('tsconfig.json', () => {
  it('should have a valid TypeScript configuration', () => {
    const config = require('../tsconfig.json');
    expect(config.compilerOptions).toBeDefined();
    expect(config.compilerOptions.target).toBe('es5');
    expect(config.compilerOptions.module).toBe('esnext');
  });
});
