## REGLES STACK — nextjs-clerk-prisma

- Mocker Clerk dans les tests React:
  jest.mock('@clerk/nextjs', () => ({ ClerkProvider: ({ children }) => children }))
- Mocker APIs Clerk server:
  jest.mock('@clerk/nextjs/server', () => ({ auth: jest.fn() }))
- Utiliser node-mocks-http pour tester les Route Handlers.
