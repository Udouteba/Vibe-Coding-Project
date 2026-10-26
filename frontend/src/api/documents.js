import request from '@/utils/request'

export const listDocuments = () => request.get('/api/documents')
export const uploadDocument = (formData) => request.post('/api/documents', formData)
export const deleteDocument = (id) => request.delete(`/api/documents/${id}`)
export const reindexDocument = (id) => request.post(`/api/documents/${id}/reindex`)
export const listChunks = (id) => request.get(`/api/documents/${id}/chunks`)
