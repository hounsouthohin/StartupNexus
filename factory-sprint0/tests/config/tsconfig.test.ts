// Since tsconfig.json is a configuration file for TypeScript, it doesn't require unit tests.
// However, we can validate its structure and content using a simple script if needed.

describe('tsconfig.json', () => {
  it('should have the correct compiler options', () => {
    const tsconfig = require('../../tsconfig.json');
    expect(tsconfig.compilerOptions).toBeDefined();
    expect(tsconfig.compilerOptions.target).toBe('es5');
    expect(tsconfig.compilerOptions.lib).toContain('dom');
    expect(tsconfig.compilerOptions.lib).toContain('dom.iterable');
    expect(tsconfig.compilerOptions.lib).toContain('esnext');
    expect(tsconfig.compilerOptions.allowJs).toBe(true);
    expect(tsconfig.compilerOptions.skipLibCheck).toBe(true);
    expect(tsconfig.compilerOptions.strict).toBe(true);
    expect(tsconfig.compilerOptions.forceConsistentCasingInFileNames).toBe(true);
    expect(tsconfig.compilerOptions.noEmit).toBe(true);
    expect(tsconfig.compilerOptions.esModuleInterop).toBe(true);
    expect(tsconfig.compilerOptions.module).toBe('esnext');
    expect(tsconfig.compilerOptions.moduleResolution).toBe('node');
    expect(tsconfig.compilerOptions.resolveJsonModule).toBe(true);
    expect(tsconfig.compilerOptions.isolatedModules).toBe(true);
    expect(tsconfig.compilerOptions.jsx).toBe('react-jsx');
    expect(tsconfig.compilerOptions.incremental).toBe(true);
    expect(tsconfig.compilerOptions.paths).toEqual({
      '@/*': ['./src/*'],
    });
  });

  it('should include the correct files', () => {
    const tsconfig = require('../../tsconfig.json');
    expect(tsconfig.include).toContain('next-env.d.ts');
    expect(tsconfig.include).toContain('**/*.ts');
    expect(tsconfig.include).toContain('**/*.tsx');
  });

  it('should exclude node_modules', () => {
    const tsconfig = require('../../tsconfig.json');
    expect(tsconfig.exclude).toContain('node_modules');
  });
});
