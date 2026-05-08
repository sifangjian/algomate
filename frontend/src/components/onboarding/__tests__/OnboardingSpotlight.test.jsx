import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import OnboardingSpotlight from '../OnboardingSpotlight'

describe('OnboardingSpotlight', () => {
  let mockElement

  beforeEach(() => {
    mockElement = document.createElement('div')
    mockElement.setAttribute('data-npc-name', '老夫子')
    mockElement.getBoundingClientRect = vi.fn(() => ({
      top: 100,
      left: 100,
      width: 200,
      height: 150,
      bottom: 250,
      right: 300,
      x: 100,
      y: 100,
    }))
    mockElement.scrollIntoView = vi.fn()
    vi.spyOn(document, 'querySelector').mockReturnValue(mockElement)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders overlay with spotlight hole when target element exists', () => {
    render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='老夫子']"
        tooltip={<div>引导提示</div>}
      />
    )

    expect(screen.getByText('引导提示')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: '引导高亮区域' })).toBeInTheDocument()
  })

  it('renders nothing when target element does not exist', () => {
    vi.restoreAllMocks()
    vi.spyOn(document, 'querySelector').mockReturnValue(null)

    const { container } = render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='不存在的NPC']"
        tooltip={<div>引导提示</div>}
      />
    )

    expect(container.innerHTML).toBe('')
  })

  it('positions spotlight hole around target element with padding', () => {
    render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='老夫子']"
        tooltip={<div>引导提示</div>}
      />
    )

    const region = screen.getByRole('region', { name: '引导高亮区域' })
    const hole = region.firstChild
    expect(hole).toBeInTheDocument()
    expect(hole.style.top).toBe('92px')
    expect(hole.style.left).toBe('92px')
    expect(hole.style.width).toBe('216px')
    expect(hole.style.height).toBe('166px')
  })

  it('renders tooltip below the spotlight hole', () => {
    render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='老夫子']"
        tooltip={<div>选择导师</div>}
      />
    )

    expect(screen.getByText('选择导师')).toBeInTheDocument()
  })

  it('calls onInteract when target element is clicked', () => {
    const mockOnInteract = vi.fn()

    render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='老夫子']"
        tooltip={<div>引导提示</div>}
        onInteract={mockOnInteract}
      />
    )

    const clickEvent = new MouseEvent('click', { bubbles: true })
    Object.defineProperty(clickEvent, 'target', { value: mockElement })
    mockElement.contains = vi.fn(() => true)
    document.dispatchEvent(clickEvent)

    expect(mockOnInteract).toHaveBeenCalledTimes(1)
  })

  it('does not call onInteract when non-target element is clicked', () => {
    const mockOnInteract = vi.fn()

    render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='老夫子']"
        tooltip={<div>引导提示</div>}
        onInteract={mockOnInteract}
      />
    )

    const clickEvent = new MouseEvent('click', { bubbles: true })
    document.dispatchEvent(clickEvent)

    expect(mockOnInteract).not.toHaveBeenCalled()
  })

  it('updates position on window resize', () => {
    render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='老夫子']"
        tooltip={<div>引导提示</div>}
      />
    )

    mockElement.getBoundingClientRect.mockReturnValue({
      top: 200, left: 200, width: 200, height: 150, bottom: 350, right: 400, x: 200, y: 200,
    })

    fireEvent(window, new Event('resize'))

    const region = screen.getByRole('region', { name: '引导高亮区域' })
    const hole = region.firstChild
    expect(hole.style.top).toBe('192px')
  })

  it('updates position on scroll', async () => {
    let rafCallback
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
      rafCallback = cb
      return 1
    })

    render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='老夫子']"
        tooltip={<div>引导提示</div>}
      />
    )

    mockElement.getBoundingClientRect.mockReturnValue({
      top: 50, left: 100, width: 200, height: 150, bottom: 200, right: 300, x: 100, y: 50,
    })

    fireEvent(window, new Event('scroll', { bubbles: true }))

    await act(async () => {
      rafCallback()
    })

    const region = screen.getByRole('region', { name: '引导高亮区域' })
    const hole = region.firstChild
    expect(hole.style.top).toBe('42px')
  })

  it('scrolls target element into view on mount', () => {
    render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='老夫子']"
        tooltip={<div>引导提示</div>}
      />
    )

    expect(mockElement.scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' })
  })

  it('positions tooltip above target when target is near viewport bottom', () => {
    mockElement.getBoundingClientRect.mockReturnValue({
      top: 700, left: 100, width: 200, height: 150, bottom: 850, right: 300, x: 100, y: 700,
    })
    vi.spyOn(window, 'innerHeight', 'get').mockReturnValue(900)

    render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='老夫子']"
        tooltip={<div>引导提示</div>}
      />
    )

    const region = screen.getByRole('region', { name: '引导高亮区域' })
    const tooltip = region.lastChild
    expect(tooltip.style.bottom).toBeDefined()
  })

  it('cleans up event listeners on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')

    const { unmount } = render(
      <OnboardingSpotlight
        targetSelector="[data-npc-name='老夫子']"
        tooltip={<div>引导提示</div>}
      />
    )

    unmount()

    expect(removeEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function))
    expect(removeEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function), true)
  })
})
