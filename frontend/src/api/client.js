const envBase = (import.meta.env.VITE_API_BASE_URL || '').trim()
let rawBase = envBase ? envBase.replace(/\/$/, '') : ''
let absoluteBase = /^https?:/i.test(rawBase)

if (absoluteBase && typeof window !== 'undefined') {
  try {
    const url = new URL(rawBase)
    const isLocalHost = ['localhost', '127.0.0.1', '0.0.0.0'].includes(url.hostname)
    const currentHost = window.location.hostname
    if (isLocalHost && currentHost && !['localhost', '127.0.0.1'].includes(currentHost)) {
      url.hostname = currentHost
      rawBase = url.toString().replace(/\/$/, '')
      absoluteBase = true
    }
  } catch (err) {
    console.warn('[API] 无法解析 VITE_API_BASE_URL，已回退到相对路径。', err)
    rawBase = ''
    absoluteBase = false
  }
}

const buildUrl = (path, params = {}) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const prefix = rawBase ? `${rawBase}${normalizedPath}` : normalizedPath
  const url = absoluteBase ? new URL(prefix) : new URL(prefix, window.location.origin)

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    url.searchParams.append(key, value)
  })

  return url.toString()
}

export const getApiBase = () => rawBase || ''

export async function request(path, options = {}) {
  const { method = 'GET', params, data, headers, signal } = options
  const url = buildUrl(path, params)

  const config = {
    method,
    headers: {
      Accept: 'application/json',
      ...(data !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...headers,
    },
    signal,
  }

  if (data !== undefined) {
    config.body = JSON.stringify(data)
  }

  const response = await fetch(url, config)
  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')
  const payload = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    const message =
      (payload && payload.error) ||
      (payload && payload.message) ||
      (typeof payload === 'string' && payload) ||
      '请求失败'
    throw new Error(message)
  }

  return payload
}
