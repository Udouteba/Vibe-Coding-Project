import request from '@/utils/request'

export const listConversations = () => request.get('/api/conversations')
export const createConversation = (data) => request.post('/api/conversations', data)
export const updateConversation = (id, data) => request.patch(`/api/conversations/${id}`, data)
export const deleteConversation = (id) => request.delete(`/api/conversations/${id}`)
export const listMessages = (id) => request.get(`/api/conversations/${id}/messages`)
