// Since tsconfig.json is a configuration file, it doesn't require unit tests.
// However, we can write a test to ensure that the TypeScript configuration is correctly set up.

describe('tsconfig.json', () => {
  it('should have the correct compiler options', () => {
    const tsconfig = require('../tsconfig.json');
    expect(tsconfig.compilerOptions.target).toBe('es5');
    expect(tsconfig.compilerOptions.lib).toEqual(['dom', 'dom.iterable', 'esnext']);
    expect(tsconfig.compilerOptions.allowJs).toBe(true);
    expect(tsconfig.compilerOptions.strict).toBe(true);
  });

  it('should include the correct files', () => {
    const tsconfig = require('../tsconfig.json');
    expect(tsconfig.include).toEqual(['next-env.d.ts', '**/*.ts', '**/*.tsx']);
  });

  it('should exclude node_modules', () => {
    const tsconfig = require('../tsconfig.json');
    expect(tsconfig.exclude).toEqual(['node_modules']);
  });
});
