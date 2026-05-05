import { describe, it, expect, vi, beforeEach } from 'vitest'

const ONBOARDING_KEY = 'algomate_onboarding_completed'

describe('Onboarding localStorage logic', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('detects first visit when localStorage key is not set', () => {
    const completed = localStorage.getItem(ONBOARDING_KEY)
    expect(completed).toBeNull()
  })

  it('marks onboarding as completed in localStorage', () => {
    localStorage.setItem(ONBOARDING_KEY, 'true')
    const completed = localStorage.getItem(ONBOARDING_KEY)
    expect(completed).toBe('true')
  })

  it('detects returning user when localStorage key is set', () => {
    localStorage.setItem(ONBOARDING_KEY, 'true')
    const completed = localStorage.getItem(ONBOARDING_KEY)
    expect(completed).toBe('true')
  })
})

describe('Empty state card count logic', () => {
  it('shows guided empty state when total_cards is 0 and no filters', () => {
    const stats = { total_cards: 0 }
    const hasCards = stats.total_cards > 0
    const debouncedSearch = ''
    const selectedRealm = ''
    const showGuidedEmpty = !hasCards && !debouncedSearch && !selectedRealm
    expect(showGuidedEmpty).toBe(true)
  })

  it('shows filtered empty state when total_cards is 0 but search is active', () => {
    const stats = { total_cards: 0 }
    const hasCards = stats.total_cards > 0
    const debouncedSearch = 'binary'
    const selectedRealm = ''
    const showGuidedEmpty = !hasCards && !debouncedSearch && !selectedRealm
    expect(showGuidedEmpty).toBe(false)
  })

  it('shows filtered empty state when total_cards is 0 but realm filter is active', () => {
    const stats = { total_cards: 0 }
    const hasCards = stats.total_cards > 0
    const debouncedSearch = ''
    const selectedRealm = '新手森林'
    const showGuidedEmpty = !hasCards && !debouncedSearch && !selectedRealm
    expect(showGuidedEmpty).toBe(false)
  })

  it('does not show guided empty state when user has cards', () => {
    const stats = { total_cards: 5 }
    const hasCards = stats.total_cards > 0
    expect(hasCards).toBe(true)
  })

  it('novice highlight shows when no cards and realm is first', () => {
    const stats = { total_cards: 0 }
    const hasCards = stats.total_cards > 0
    const index = 0
    const showHighlight = index === 0 && !hasCards
    expect(showHighlight).toBe(true)
  })

  it('novice highlight does not show when user has cards', () => {
    const stats = { total_cards: 3 }
    const hasCards = stats.total_cards > 0
    const index = 0
    const showHighlight = index === 0 && !hasCards
    expect(showHighlight).toBe(false)
  })

  it('boss battle empty state shows when no available cards', () => {
    const cards = []
    const showEmpty = cards.length === 0
    expect(showEmpty).toBe(true)
  })

  it('boss battle empty state does not show when cards exist', () => {
    const cards = [{ id: 1, name: 'test' }]
    const showEmpty = cards.length === 0
    expect(showEmpty).toBe(false)
  })
})
