import './globals.css';
import { ClerkProvider } from '@clerk/nextjs';

export const metadata = {
    title: 'Project Management App',
    description: 'A web-based application for project management.'
};

const RootLayout = ({ children }) => {
    return (
        <ClerkProvider>
            <html lang="en">
                <body>{children}</body>
            </html>
        </ClerkProvider>
    );
};

export default RootLayout;