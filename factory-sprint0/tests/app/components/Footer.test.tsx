import { render } from '@testing-library/react';
import Footer from '../../../app/components/Footer';

describe('Footer', () => {
  it('renders the footer with the correct text', () => {
    const { getByText } = render(<Footer />);
    expect(getByText(/Â© 2023 Todo Batch Alpha/i)).toBeInTheDocument();
  });
});
