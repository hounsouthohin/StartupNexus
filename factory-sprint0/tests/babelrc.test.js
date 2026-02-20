// .babelrc is a configuration file for Babel, and typically doesn't require unit tests.
// However, we can write a test to ensure that the configuration is valid if needed.

describe('.babelrc', () => {
  it('should have a valid Babel configuration', () => {
    const config = require('../.babelrc');
    expect(config.presets).toContain('next/babel');
  });
});
