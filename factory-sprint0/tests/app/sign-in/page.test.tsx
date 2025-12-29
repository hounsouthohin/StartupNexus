import { render } from '@testing-library/react';
import SignInPage from '../../../app/sign-in/page';
import { SignIn } from '@clerk/nextjs';

jest.mock('@clerk/nextjs', () => ({
  SignIn: () => <div>Sign In Component</div>,
}));

describe('SignInPage', () => {
  it('should render SignIn component', () => {
    const { container } = render(<SignInPage />);
    expect(container).toHaveTextContent('Sign In Component');
  });
});
