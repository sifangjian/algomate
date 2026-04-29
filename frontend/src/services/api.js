import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
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
      case 500:
        throw new Error(data?.detail || '服务器繁忙，请稍后再试')
      default:
        throw new Error(
          data?.message || data?.error || data?.detail || `请求失败 (${status})`
        )
    }
  }
)

export default api
