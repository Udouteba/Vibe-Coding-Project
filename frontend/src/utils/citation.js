export function formatCitation(item) {
  let s = `《${item.title || ''}》`
  if (item.code) s += ` ${item.code}`
  if (item.version) s += `（${item.version}版）`
  if (item.chapter) s += ` ${item.chapter}`
  if (item.clause) s += ` ${item.clause}`
  return s
}

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    return true
  }
}
