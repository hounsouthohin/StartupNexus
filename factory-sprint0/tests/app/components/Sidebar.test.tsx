import { render } from '@testing-library/react';
import Sidebar from '../../../app/components/Sidebar';

describe('Sidebar', () => {
  it('renders the sidebar with the correct text', () => {
    const { getByText } = render(<Sidebar />);
    expect(getByText('Sidebar')).toBeInTheDocument();
  });
});
