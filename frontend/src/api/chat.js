import { getToken } from '@/utils/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

function parseSSE(block) {
  let event = 'message'
  const dataLines = []
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
  }
  if (dataLines.length === 0) return null
  try {
    return { event, data: JSON.parse(dataLines.join('\n')) }
  } catch {
    return { event, data: dataLines.join('\n') }
  }
}

export async function streamChat({ conversationId, message, documentIds, onEvent }) {
  const res = await fetch(`${baseURL}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken()}`
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
      document_ids: documentIds
    })
  })
  if (!res.ok) {
    throw new Error(`请求失败: ${res.status}`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''
    for (const block of blocks) {
      const parsed = parseSSE(block)
      if (parsed) onEvent(parsed)
    }
  }
}
