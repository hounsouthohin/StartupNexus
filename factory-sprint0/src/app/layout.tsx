import { ClerkProvider } from '@clerk/nextjs';
import { ReactNode } from 'react';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider>
      <div className="min-h-screen bg-gray-100">
        {children}
      </div>
    </ClerkProvider>
  );
}