import type { Metadata } from 'next';
import { TITRE } from '@/lib/droits';
import './globals.css';

export const metadata: Metadata = { title: TITRE };

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="fr">
            <body className="min-h-screen">{children}</body>
        </html>
    );
}
