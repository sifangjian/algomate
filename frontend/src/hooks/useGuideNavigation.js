import { useNavigate } from 'react-router-dom'

export function useGuideNavigation() {
  const navigate = useNavigate()

  const navigateToAction = (action) => {
    if (!action?.target_path) return

    const path = action.target_path
    const params = action.params || {}

    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      searchParams.set(key, String(value))
    })

    const queryString = searchParams.toString()
    navigate(queryString ? `${path}?${queryString}` : path)
  }

  return { navigateToAction }
}
