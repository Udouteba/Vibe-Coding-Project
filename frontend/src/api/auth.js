import request from '@/utils/request'

export const register = (data) => request.post('/api/auth/register', data)
export const login = (data) => request.post('/api/auth/login', data)
export const changePassword = (data) => request.post('/api/auth/change-password', data)
export const getMe = () => request.get('/api/auth/me')
