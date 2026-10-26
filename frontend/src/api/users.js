import request from '@/utils/request'

export const listUsers = () => request.get('/api/users')
export const createUser = (data) => request.post('/api/users', data)
export const updateUser = (id, data) => request.patch(`/api/users/${id}`, data)
export const deleteUser = (id) => request.delete(`/api/users/${id}`)
