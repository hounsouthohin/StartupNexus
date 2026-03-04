/**
 * Tests structurels du middleware Clerk v6.
 *
 * Le middleware s'exécute dans le Edge Runtime de Next.js — il n'est pas
 * unit-testable avec jest/jsdom (NextRequest, NextResponse, crypto.subtle…).
 * Ce fichier valide UNIQUEMENT les exports (structure), pas le comportement runtime.
 */

// jest.mock est hoissté avant les imports par le transform Babel/ts-jest.
jest.mock('@clerk/nextjs/server', () => ({
  clerkMiddleware: jest.fn((handler) => jest.fn()),
  createRouteMatcher: jest.fn(() => jest.fn(() => false)),
}));

describe('middleware — exports structurels', () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const mod = require('../middleware');
  const middleware = mod.default ?? mod;

  it('exporte une fonction middleware par défaut', () => {
    expect(typeof middleware).toBe('function');
  });

  it('exporte un objet config avec un tableau matcher', () => {
    expect(mod.config).toBeDefined();
    expect(Array.isArray(mod.config.matcher)).toBe(true);
    expect(mod.config.matcher.length).toBeGreaterThan(0);
  });
});
