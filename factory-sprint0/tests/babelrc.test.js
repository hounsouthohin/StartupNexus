// .babelrc is a configuration file, so we don't typically write unit tests for it.
// However, we can write a test to ensure that the Babel configuration is correctly set up.

describe('.babelrc', () => {
  it('should have the correct presets', () => {
    const babelrc = require('../.babelrc');
    expect(babelrc.presets).toEqual(['next/babel']);
  });
});
