import { render, screen } from '@testing-library/react';
import DashboardPage from '../../../app/dashboard/page';
import { useUser } from '@clerk/nextjs';

jest.mock('@clerk/nextjs', () => ({
  useUser: jest.fn(),
}));

describe('DashboardPage', () => {
  it('should render welcome message with user first name', () => {
    (useUser as jest.Mock).mockReturnValue({ user: { firstName: 'John' } });
    render(<DashboardPage />);
    expect(screen.getByText('Welcome, John')).toBeInTheDocument();
  });

  it('should render welcome message without user first name if user is undefined', () => {
    (useUser as jest.Mock).mockReturnValue({ user: undefined });
    render(<DashboardPage />);
    expect(screen.getByText('Welcome,')).toBeInTheDocument();
  });
});
