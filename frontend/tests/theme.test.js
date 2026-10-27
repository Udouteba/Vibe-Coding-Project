import { describe, it, expect } from 'vitest'
import { applyTheme, forceLight } from '@/utils/theme'

describe('applyTheme', () => {
  it('暗色添加 dark class', () => {
    applyTheme(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('亮色移除 dark class', () => {
    applyTheme(true)
    applyTheme(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})

describe('forceLight', () => {
  it('强制亮色', () => {
    document.documentElement.classList.add('dark')
    forceLight()
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
