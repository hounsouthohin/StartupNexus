import { render } from '@testing-library/react';
import RootLayout from '../../app/layout';
import { ClerkProvider } from '@clerk/nextjs';

jest.mock('@clerk/nextjs', () => ({
  ClerkProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('RootLayout', () => {
  it('renders children inside ClerkProvider', () => {
    const { getByText } = render(
      <RootLayout>
        <div>Test Child</div>
      </RootLayout>
    );
    expect(getByText('Test Child')).toBeInTheDocument();
  });
});
