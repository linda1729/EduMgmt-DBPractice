import { request } from './client'

export const fetchDashboardSummary = () => request('/api/v1/analytics/dashboard')
