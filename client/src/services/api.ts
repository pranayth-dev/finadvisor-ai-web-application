import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auth endpoints that are allowed to return 401 without triggering a logout.
// A 401 from /auth/login just means wrong password — it must NOT redirect.
const AUTH_ENDPOINTS = ['/auth/login', '/auth/register']

// Handle 401 (session expired) — but only for authenticated requests.
// If the 401 came from a login/register call, let it propagate to the caller
// so the form can show "Invalid email or password." and stay on the page.
api.interceptors.response.use(
  (res) => res,
  (error) => {
    const url: string = error.config?.url ?? ''
    const isAuthCall = AUTH_ENDPOINTS.some((p) => url.includes(p))

    if (error.response?.status === 401 && !isAuthCall) {
      // An authenticated request was rejected — session has expired or token
      // was tampered with.  Clear stored credentials and let React Router
      // redirect naturally on the next render (RequireAuth → Navigate /landing).
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      // Dispatch a custom event so AuthProvider can react without a hard reload
      window.dispatchEvent(new Event('auth:expired'))
    }

    return Promise.reject(error)
  }
)

export default api
