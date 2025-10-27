/**
 * Footer Component Tests
 *
 * Coverage-Gap-Agent - Wave 4, Task 23
 * Testing footer with theme controls and connection status
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Footer from '../Footer'

// Mock child components
vi.mock('../../common/ThemeToggle', () => ({
  default: () => <div data-testid="theme-toggle">Theme Toggle</div>,
}))

vi.mock('../../common/StyleSelector', () => ({
  default: () => <div data-testid="style-selector">Style Selector</div>,
}))

vi.mock('../../common/ConnectionStatus', () => ({
  default: () => <div data-testid="connection-status">Connection Status</div>,
}))

describe('Footer Component', () => {
  describe('Basic Rendering', () => {
    it('renders footer with default props', () => {
      render(<Footer />)

      const footer = screen.getByRole('contentinfo')
      expect(footer).toBeInTheDocument()
      expect(footer).toHaveClass('footer')
    })

    it('renders footer container', () => {
      const { container } = render(<Footer />)

      const footerContainer = container.querySelector('.footer__container')
      expect(footerContainer).toBeInTheDocument()
    })

    it('renders actions section', () => {
      const { container } = render(<Footer />)

      const actions = container.querySelector('.footer__actions')
      expect(actions).toBeInTheDocument()
    })
  })

  describe('Child Components', () => {
    it('renders ThemeToggle component', () => {
      render(<Footer />)

      expect(screen.getByTestId('theme-toggle')).toBeInTheDocument()
    })

    it('renders StyleSelector component', () => {
      render(<Footer />)

      expect(screen.getByTestId('style-selector')).toBeInTheDocument()
    })

    it('renders ConnectionStatus by default', () => {
      render(<Footer />)

      expect(screen.getByTestId('connection-status')).toBeInTheDocument()
    })
  })

  describe('Connection Status Visibility', () => {
    it('shows connection status when showConnectionStatus is true', () => {
      render(<Footer showConnectionStatus={true} />)

      expect(screen.getByTestId('connection-status')).toBeInTheDocument()
    })

    it('hides connection status when showConnectionStatus is false', () => {
      render(<Footer showConnectionStatus={false} />)

      expect(screen.queryByTestId('connection-status')).not.toBeInTheDocument()
    })

    it('shows connection status by default', () => {
      render(<Footer />)

      expect(screen.getByTestId('connection-status')).toBeInTheDocument()
    })

    it('renders status container when showing connection status', () => {
      const { container } = render(<Footer showConnectionStatus={true} />)

      const statusContainer = container.querySelector('.footer__status')
      expect(statusContainer).toBeInTheDocument()
    })

    it('does not render status container when hiding connection status', () => {
      const { container } = render(<Footer showConnectionStatus={false} />)

      const statusContainer = container.querySelector('.footer__status')
      expect(statusContainer).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has role="contentinfo" on footer', () => {
      render(<Footer />)

      const footer = screen.getByRole('contentinfo')
      expect(footer).toBeInTheDocument()
    })

    it('footer is accessible via landmark navigation', () => {
      render(<Footer />)

      const contentinfo = screen.getByRole('contentinfo')
      expect(contentinfo.tagName).toBe('FOOTER')
    })
  })

  describe('Layout Structure', () => {
    it('renders all components in correct order', () => {
      const { container } = render(<Footer />)

      const actions = container.querySelector('.footer__actions')
      const status = container.querySelector('.footer__status')

      expect(actions).toBeInTheDocument()
      expect(status).toBeInTheDocument()

      // Actions should come before status
      const containerChildren = Array.from(container.querySelector('.footer__container').children)
      const actionsIndex = containerChildren.indexOf(actions)
      const statusIndex = containerChildren.indexOf(status)

      expect(actionsIndex).toBeLessThan(statusIndex)
    })

    it('theme toggle and style selector are in actions section', () => {
      const { container } = render(<Footer />)

      const actions = container.querySelector('.footer__actions')
      const themeToggle = screen.getByTestId('theme-toggle')
      const styleSelector = screen.getByTestId('style-selector')

      expect(actions).toContainElement(themeToggle)
      expect(actions).toContainElement(styleSelector)
    })

    it('connection status is in status section when visible', () => {
      const { container } = render(<Footer />)

      const status = container.querySelector('.footer__status')
      const connectionStatus = screen.getByTestId('connection-status')

      expect(status).toContainElement(connectionStatus)
    })
  })

  describe('Edge Cases', () => {
    it('handles showConnectionStatus as undefined', () => {
      render(<Footer showConnectionStatus={undefined} />)

      // Should default to true
      expect(screen.getByTestId('connection-status')).toBeInTheDocument()
    })

    it('handles showConnectionStatus as null', () => {
      render(<Footer showConnectionStatus={null} />)

      // Null is falsy, should hide
      expect(screen.queryByTestId('connection-status')).not.toBeInTheDocument()
    })

    it('handles showConnectionStatus as truthy value', () => {
      render(<Footer showConnectionStatus={1} />)

      expect(screen.getByTestId('connection-status')).toBeInTheDocument()
    })

    it('handles showConnectionStatus as falsy value', () => {
      render(<Footer showConnectionStatus={0} />)

      expect(screen.queryByTestId('connection-status')).not.toBeInTheDocument()
    })
  })

  describe('CSS Classes', () => {
    it('applies correct CSS class to footer', () => {
      render(<Footer />)

      const footer = screen.getByRole('contentinfo')
      expect(footer).toHaveClass('footer')
    })

    it('applies correct CSS class to container', () => {
      const { container } = render(<Footer />)

      const footerContainer = container.querySelector('.footer__container')
      expect(footerContainer).toBeInTheDocument()
    })

    it('applies correct CSS class to actions', () => {
      const { container } = render(<Footer />)

      const actions = container.querySelector('.footer__actions')
      expect(actions).toHaveClass('footer__actions')
    })

    it('applies correct CSS class to status section', () => {
      const { container } = render(<Footer />)

      const status = container.querySelector('.footer__status')
      expect(status).toHaveClass('footer__status')
    })
  })
})
