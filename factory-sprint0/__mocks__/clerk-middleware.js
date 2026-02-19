module.exports = {
  withClerkMiddleware: (handler) => handler,
  clerkMiddleware: (handler) => handler, // Added per Grok's suggestion
};