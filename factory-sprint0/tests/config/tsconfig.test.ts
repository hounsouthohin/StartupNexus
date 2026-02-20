describe('tsconfig.json', () => {
  it('should have correct compiler options', () => {
    const tsconfig = require('../../tsconfig.json');
    expect(tsconfig.compilerOptions.target).toBe('es5');
    expect(tsconfig.compilerOptions.lib).toEqual(['dom', 'dom.iterable', 'esnext']);
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

  it('should include correct files', () => {
    const tsconfig = require('../../tsconfig.json');
    expect(tsconfig.include).toEqual(['next-env.d.ts', '**/*.ts', '**/*.tsx']);
  });

  it('should exclude node_modules', () => {
    const tsconfig = require('../../tsconfig.json');
    expect(tsconfig.exclude).toEqual(['node_modules']);
  });
});
