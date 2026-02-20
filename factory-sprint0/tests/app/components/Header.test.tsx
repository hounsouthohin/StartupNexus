import { render } from '@testing-library/react';
import Header from '../../../app/components/Header';

describe('Header', () => {
  it('renders the header with the correct text', () => {
    const { getByText } = render(<Header />);
    expect(getByText('Todo Batch Alpha')).toBeInTheDocument();
  });
});
