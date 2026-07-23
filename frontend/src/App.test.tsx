import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders the hero title', () => {
    render(<App />)
    expect(screen.getByText(/Change Impact/i)).toBeTruthy()
  })

  it('renders mode toggle buttons', () => {
    render(<App />)
    expect(screen.getByText('Chat Mode')).toBeTruthy()
    expect(screen.getByText('Form Mode')).toBeTruthy()
  })

  it('renders the initial assistant message', () => {
    render(<App />)
    expect(screen.getByText(/AI Change Impact Analyzer/i)).toBeTruthy()
  })
})

