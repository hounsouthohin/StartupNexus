// Babel configuration is typically not unit tested, but we can check if the configuration is loaded correctly.

describe('Babel Configuration', () => {
  it('should have the correct presets', () => {
    const babelConfig = require('../../.babelrc');
    expect(babelConfig.presets).toContain('next/babel');
  });
});
