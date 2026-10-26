import request from '@/utils/request'

export const listCategories = () => request.get('/api/categories')
