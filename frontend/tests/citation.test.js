import { describe, it, expect } from 'vitest'
import { formatCitation } from '@/utils/citation'

describe('formatCitation', () => {
  it('完整引用', () => {
    expect(
      formatCitation({
        title: '建筑给水排水设计标准',
        code: 'GB 50015',
        version: '2019',
        chapter: '第三章',
        clause: '3.1.2'
      })
    ).toBe('《建筑给水排水设计标准》 GB 50015（2019版） 第三章 3.1.2')
  })

  it('最小引用', () => {
    expect(formatCitation({ title: '规范' })).toBe('《规范》')
  })

  it('无 title 返回空书名号', () => {
    expect(formatCitation({})).toBe('《》')
  })

  it('空字段不追加', () => {
    expect(formatCitation({ title: '规范', code: '', version: '', chapter: '', clause: '' })).toBe(
      '《规范》'
    )
  })
})
