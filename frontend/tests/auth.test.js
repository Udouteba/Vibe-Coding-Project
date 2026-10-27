import { describe, it, expect, beforeEach } from 'vitest'
import { getToken, setToken, getUserInfo, setUserInfo, isAdmin, logout } from '@/utils/auth'

beforeEach(() => {
  localStorage.clear()
})

describe('token', () => {
  it('设置与读取', () => {
    setToken('abc')
    expect(getToken()).toBe('abc')
  })
})

describe('userInfo', () => {
  it('设置与读取', () => {
    setUserInfo({ username: 'admin', role: 'admin' })
    expect(getUserInfo()).toEqual({ username: 'admin', role: 'admin' })
  })

  it('非法 JSON 返回 null', () => {
    localStorage.setItem('drainage_user', 'not-json')
    expect(getUserInfo()).toBeNull()
  })
})

describe('isAdmin', () => {
  it('admin 角色返回 true', () => {
    setUserInfo({ role: 'admin' })
    expect(isAdmin()).toBe(true)
  })

  it('非 admin 返回 false', () => {
    setUserInfo({ role: 'student' })
    expect(isAdmin()).toBe(false)
  })

  it('无用户信息返回 false', () => {
    expect(isAdmin()).toBe(false)
  })
})

describe('logout', () => {
  it('清除 token 与用户信息', () => {
    setToken('abc')
    setUserInfo({ role: 'admin' })
    logout()
    expect(getToken()).toBeNull()
    expect(getUserInfo()).toBeNull()
  })
})
