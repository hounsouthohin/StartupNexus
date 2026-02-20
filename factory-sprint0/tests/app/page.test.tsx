import { render } from '@testing-library/react';
import HomePage from '../../app/page';

describe('HomePage', () => {
  it('renders the homepage with header and footer', () => {
    const { getByText } = render(<HomePage />);
    expect(getByText('Todo Batch Alpha')).toBeInTheDocument();
    expect(getByText('Welcome to Todo Batch Alpha')).toBeInTheDocument();
    expect(getByText(/Â© 2023 Todo Batch Alpha/i)).toBeInTheDocument();
  });
});
