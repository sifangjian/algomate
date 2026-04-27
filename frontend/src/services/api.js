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
      throw new Error('网络连接失败，请检查网络')
    }
    switch (error.response.status) {
      case 401:
        localStorage.removeItem('auth_token')
        window.location.href = '/login'
        break
      case 403:
        throw new Error('您没有权限执行此操作')
      case 404:
        throw new Error('请求的资源不存在')
      case 500:
        throw new Error('服务器繁忙，请稍后再试')
      default:
        throw new Error(
          error.response.data?.message || error.response.data?.error || '请求失败'
        )
    }
  }
)

export default api
