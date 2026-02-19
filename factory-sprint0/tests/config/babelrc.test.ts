// .babelrc is a configuration file for Babel, typically not unit tested.

describe('.babelrc', () => {
  it('should have the correct presets', () => {
    const babelrc = require('../../.babelrc');
    expect(babelrc.presets).toContain('next/babel');
  });
});
