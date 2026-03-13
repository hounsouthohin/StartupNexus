import { ClerkProvider } from "@clerk/nextjs";
import type { ReactNode } from "react";

export default function Layout({ children }: { children: ReactNode }) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const canUseClerk =
    typeof publishableKey === "string" &&
    publishableKey.startsWith("pk_") &&
    !publishableKey.includes("placeholder");

  if (!canUseClerk) {
    return (
      <html lang="en">
        <body>{children}</body>
      </html>
    );
  }

  return (
    <ClerkProvider publishableKey={publishableKey}>
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
