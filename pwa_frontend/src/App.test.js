import React from 'react';
import { render } from '@testing-library/react';

// Simple test component for testing
const TestComponent = () => {
  return <div data-testid="test-component">Test Component</div>;
};

test('renders test component', () => {
  const { getByTestId } = render(<TestComponent />);
  const testElement = getByTestId('test-component');
  expect(testElement).toBeInTheDocument();
  expect(testElement).toHaveTextContent('Test Component');
});
