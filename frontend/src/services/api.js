import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        console.error('Request Timeout:', error.message)
        throw new Error('请求超时，AI正在思考中，请稍后重试')
      }
      console.error('Network Error:', error.message)
      throw new Error('网络连接失败，请检查网络')
    }

    const status = error.response.status
    const data = error.response.data

    console.error(`API Error [${status}]:`, data)

    switch (status) {
      case 401:
        localStorage.removeItem('auth_token')
        throw new Error(data?.detail || data?.message || '认证失败，请刷新页面重试')
      case 403:
        throw new Error(data?.detail || '您没有权限执行此操作')
      case 404:
        throw new Error(data?.detail || '请求的资源不存在')
      case 429:
        throw new Error(data?.detail || '请求过于频繁，请稍后再试')
      case 500:
        throw new Error(data?.detail || '服务器繁忙，请稍后再试')
      case 504:
        throw new Error(data?.detail || 'AI服务响应超时，请稍后重试')
      default:
        throw new Error(
          data?.message || data?.error || data?.detail || `请求失败 (${status})`
        )
    }
  }
)

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const shouldRetry = (error) => {
  if (!error.response) {
    return error.code === 'ECONNABORTED' || error.message.includes('Network Error')
  }
  const status = error.response.status
  return status === 503 || status === 504 || status === 429
}

const apiWithRetry = async (requestFn, retries = 2, delay = 2000) => {
  let lastError
  for (let i = 0; i <= retries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error
      if (i < retries && shouldRetry(error)) {
        console.log(`Retry attempt ${i + 1}/${retries} after ${delay}ms`)
        await sleep(delay)
        delay *= 1.5
      } else {
        throw error
      }
    }
  }
  throw lastError
}

export { apiWithRetry }
export default api
