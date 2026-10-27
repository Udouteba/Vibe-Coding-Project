import { describe, it, expect } from 'vitest'
import { usernameError, passwordError } from '@/utils/validators'

describe('usernameError', () => {
  it('空值返回 null', () => {
    expect(usernameError('')).toBeNull()
  })

  it('合法用户名返回 null', () => {
    expect(usernameError('abcde')).toBeNull()
    expect(usernameError('user_123')).toBeNull()
    expect(usernameError('a'.repeat(20))).toBeNull()
  })

  it('长度不足', () => {
    expect(usernameError('abcd')).toBe('用户名长度需为 5~20 个字符')
  })

  it('长度超限', () => {
    expect(usernameError('a'.repeat(21))).toBe('用户名长度需为 5~20 个字符')
  })

  it('非法字符', () => {
    expect(usernameError('abcde-')).toBe('用户名只能包含英文字母、数字、下划线')
  })
})

describe('passwordError', () => {
  it('空值返回 null', () => {
    expect(passwordError('')).toBeNull()
  })

  it('合法密码返回 null', () => {
    expect(passwordError('Abc12345')).toBeNull()
  })

  it('少于 8 位', () => {
    expect(passwordError('a'.repeat(7))).toBe('密码至少 8 位')
  })

  it('超过 72 位', () => {
    expect(passwordError('a'.repeat(73))).toBe('密码不能超过 72 位')
  })

  it('非法字符', () => {
    expect(passwordError('Abc-1234')).toBe('密码只能包含英文字母、数字、下划线')
  })

  it('仅一类字符', () => {
    expect(passwordError('abcdefgh')).toBe('密码需包含大写字母、小写字母、数字中的至少两类')
  })

  it('72 位边界合法', () => {
    expect(passwordError('aA1' + 'b'.repeat(69))).toBeNull()
  })
})
