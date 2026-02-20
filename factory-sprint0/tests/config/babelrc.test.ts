describe('.babelrc', () => {
  it('should have correct presets', () => {
    const babelrc = require('../../.babelrc');
    expect(babelrc.presets).toEqual(['next/babel']);
  });
});
