import request from '@/utils/request'

export const listPresets = () => request.get('/api/presets')
export const createPreset = (data) => request.post('/api/presets', data)
export const deletePreset = (id) => request.delete(`/api/presets/${id}`)
