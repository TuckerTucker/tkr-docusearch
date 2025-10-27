/**
 * Header Component Tests
 *
 * Coverage-Gap-Agent - Wave 4, Task 23
 * Testing header rendering with dynamic content and back button
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Header from '../Header'

function renderHeader(props = {}) {
  return render(
    <BrowserRouter>
      <Header {...props} />
    </BrowserRouter>
  )
}

describe('Header Component', () => {
  describe('Basic Rendering', () => {
    it('renders header with default props', () => {
      renderHeader()

      const header = screen.getByRole('banner')
      expect(header).toBeInTheDocument()
      expect(header).toHaveClass('header')
    })

    it('renders with default title', () => {
      renderHeader()

      const title = screen.getByRole('heading', { level: 1 })
      expect(title).toHaveTextContent('Document Search')
    })

    it('renders with custom title', () => {
      renderHeader({ title: 'Custom Title' })

      const title = screen.getByRole('heading', { level: 1 })
      expect(title).toHaveTextContent('Custom Title')
    })

    it('does not render title when title is empty string', () => {
      renderHeader({ title: '' })

      const titles = screen.queryAllByRole('heading', { level: 1 })
      expect(titles).toHaveLength(0)
    })

    it('does not render title when title is null', () => {
      renderHeader({ title: null })

      const titles = screen.queryAllByRole('heading', { level: 1 })
      expect(titles).toHaveLength(0)
    })
  })

  describe('Back Button', () => {
    it('does not show back button by default', () => {
      renderHeader()

      const backButton = screen.queryByRole('link', { name: 'Go back' })
      expect(backButton).not.toBeInTheDocument()
    })

    it('shows back button when showBackButton is true', () => {
      renderHeader({ showBackButton: true })

      const backButton = screen.getByRole('link', { name: 'Go back' })
      expect(backButton).toBeInTheDocument()
    })

    it('back button links to default route', () => {
      renderHeader({ showBackButton: true })

      const backButton = screen.getByRole('link', { name: 'Go back' })
      expect(backButton).toHaveAttribute('href', '/')
    })

    it('back button links to custom route', () => {
      renderHeader({ showBackButton: true, backTo: '/custom' })

      const backButton = screen.getByRole('link', { name: 'Go back' })
      expect(backButton).toHaveAttribute('href', '/custom')
    })

    it('back button has correct aria-label', () => {
      renderHeader({ showBackButton: true })

      const backButton = screen.getByRole('link', { name: 'Go back' })
      expect(backButton).toHaveAttribute('aria-label', 'Go back')
    })

    it('back button contains text "Back to Library"', () => {
      renderHeader({ showBackButton: true })

      expect(screen.getByText('Back to Library')).toBeInTheDocument()
    })

    it('back button has correct CSS class', () => {
      renderHeader({ showBackButton: true })

      const backButton = screen.getByRole('link', { name: 'Go back' })
      expect(backButton).toHaveClass('header__back-button')
    })

    it('back button contains SVG icon', () => {
      const { container } = renderHeader({ showBackButton: true })

      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })
  })

  describe('Filter Bar', () => {
    it('does not render filter bar by default', () => {
      const { container } = renderHeader()

      const filterBar = container.querySelector('.header__filter-bar')
      expect(filterBar).not.toBeInTheDocument()
    })

    it('renders filter bar when provided', () => {
      const FilterBar = () => <div data-testid="filter">Filter Content</div>
      renderHeader({ filterBar: <FilterBar /> })

      expect(screen.getByTestId('filter')).toBeInTheDocument()
    })

    it('renders custom filter bar content', () => {
      renderHeader({ filterBar: <div>Custom Filter</div> })

      expect(screen.getByText('Custom Filter')).toBeInTheDocument()
    })

    it('wraps filter bar in correct container', () => {
      const { container } = renderHeader({ filterBar: <div>Filter</div> })

      const filterBarContainer = container.querySelector('.header__filter-bar')
      expect(filterBarContainer).toBeInTheDocument()
      expect(filterBarContainer).toHaveTextContent('Filter')
    })
  })

  describe('Layout and Structure', () => {
    it('has correct container structure', () => {
      const { container } = renderHeader()

      const headerContainer = container.querySelector('.header__container')
      expect(headerContainer).toBeInTheDocument()
    })

    it('has correct left section', () => {
      const { container } = renderHeader()

      const leftSection = container.querySelector('.header__left')
      expect(leftSection).toBeInTheDocument()
    })

    it('title has correct CSS class', () => {
      renderHeader({ title: 'Test' })

      const title = screen.getByRole('heading', { level: 1 })
      expect(title).toHaveClass('header__title')
    })
  })

  describe('Combined States', () => {
    it('renders back button and title together', () => {
      renderHeader({ showBackButton: true, title: 'Page Title' })

      expect(screen.getByRole('link', { name: 'Go back' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Page Title')
    })

    it('renders all elements together', () => {
      renderHeader({
        showBackButton: true,
        title: 'Test Page',
        filterBar: <div>Filter</div>,
      })

      expect(screen.getByRole('link', { name: 'Go back' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Test Page')
      expect(screen.getByText('Filter')).toBeInTheDocument()
    })

    it('renders only filter bar when title is empty', () => {
      renderHeader({
        title: '',
        filterBar: <div>Filter Only</div>,
      })

      expect(screen.queryByRole('heading')).not.toBeInTheDocument()
      expect(screen.getByText('Filter Only')).toBeInTheDocument()
    })

    it('renders only back button and title when no filter bar', () => {
      renderHeader({
        showBackButton: true,
        title: 'Title Only',
        filterBar: null,
      })

      expect(screen.getByRole('link', { name: 'Go back' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
      const { container } = render(<div />)
      expect(container.querySelector('.header__filter-bar')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has role="banner" on header', () => {
      renderHeader()

      const header = screen.getByRole('banner')
      expect(header).toBeInTheDocument()
    })

    it('SVG icon has aria-hidden', () => {
      const { container } = renderHeader({ showBackButton: true })

      const svg = container.querySelector('svg')
      expect(svg).toHaveAttribute('aria-hidden', 'true')
    })

    it('back button has accessible label', () => {
      renderHeader({ showBackButton: true })

      const backButton = screen.getByRole('link', { name: 'Go back' })
      expect(backButton).toHaveAccessibleName('Go back')
    })

    it('title is properly announced by screen readers', () => {
      renderHeader({ title: 'Accessible Title' })

      const title = screen.getByRole('heading', { level: 1, name: 'Accessible Title' })
      expect(title).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles undefined props gracefully', () => {
      renderHeader({
        title: undefined,
        showBackButton: undefined,
        backTo: undefined,
        filterBar: undefined,
      })

      const header = screen.getByRole('banner')
      expect(header).toBeInTheDocument()
    })

    it('handles null filterBar', () => {
      renderHeader({ filterBar: null })

      const { container } = render(<div />)
      expect(container.querySelector('.header__filter-bar')).not.toBeInTheDocument()
    })

    it('handles false showBackButton', () => {
      renderHeader({ showBackButton: false })

      expect(screen.queryByRole('link', { name: 'Go back' })).not.toBeInTheDocument()
    })

    it('handles backTo with different route formats', () => {
      const routes = ['/details/123', '/research', '/search?q=test']

      routes.forEach((route) => {
        const { unmount } = renderHeader({ showBackButton: true, backTo: route })
        const backButton = screen.getByRole('link', { name: 'Go back' })
        expect(backButton).toHaveAttribute('href', route)
        unmount()
      })
    })
  })
})
