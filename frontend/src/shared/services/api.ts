import axios, {
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'

// ---------------------------------------------------------------------------
// Token in-memory store (never in localStorage — safer against XSS)
// ---------------------------------------------------------------------------
let _accessToken: string | null = null

export function getAccessToken(): string | null {
  return _accessToken
}

export function setAccessToken(token: string | null): void {
  _accessToken = token
}

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------
export const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL as string,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Request interceptor — attach Bearer token
// ---------------------------------------------------------------------------
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

// ---------------------------------------------------------------------------
// Response interceptor — silent token refresh on 401
// ---------------------------------------------------------------------------
type QueueEntry = {
  resolve: (token: string) => void
  reject: (err: unknown) => void
}

let isRefreshing = false
const failedQueue: QueueEntry[] = []

function processQueue(error: unknown, token: string | null): void {
  failedQueue.forEach((entry) => {
    if (error) {
      entry.reject(error)
    } else {
      entry.resolve(token as string)
    }
  })
  failedQueue.length = 0
}

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) return Promise.reject(error)

    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // Only intercept 401s that haven't been retried yet
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    // Skip refresh for the refresh endpoint itself to avoid infinite loops
    if (originalRequest.url?.includes('/api/auth/refresh')) {
      clearSession()
      return Promise.reject(error)
    }

    if (isRefreshing) {
      // Enqueue and wait for the in-flight refresh to finish
      return new Promise<AxiosResponse>((resolve, reject) => {
        failedQueue.push({
          resolve: (token: string) => {
            originalRequest.headers.set('Authorization', `Bearer ${token}`)
            originalRequest._retry = true
            resolve(api(originalRequest))
          },
          reject,
        })
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const refreshToken = localStorage.getItem('rt')
      if (!refreshToken) {
        clearSession()
        return Promise.reject(error)
      }

      const { data } = await axios.post<{ access_token: string }>(
        `${import.meta.env.VITE_API_BASE_URL as string}/api/auth/refresh`,
        { refresh_token: refreshToken },
      )

      setAccessToken(data.access_token)
      processQueue(null, data.access_token)

      originalRequest.headers.set(
        'Authorization',
        `Bearer ${data.access_token}`,
      )
      return api(originalRequest)
    } catch (refreshError) {
      processQueue(refreshError, null)
      clearSession()
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)

// ---------------------------------------------------------------------------
// Session cleanup helper (imported by useAuth for logout)
// ---------------------------------------------------------------------------
export function clearSession(): void {
  setAccessToken(null)
  localStorage.removeItem('rt')
  // Redirect to login — use location.replace so back-button doesn't return
  window.location.replace('/login')
}
