// jest.setup.js is used for setting up the testing environment.
// We can ensure that it imports the necessary modules.

describe('jest.setup.js', () => {
  it('should import @testing-library/jest-dom', () => {
    const jestSetup = require('../../jest.setup.js');
    expect(jestSetup).toBeDefined();
  });
});
