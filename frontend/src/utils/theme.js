// 应用主题：true 为暗色，false 为亮色
export function applyTheme(isDark) {
  document.documentElement.classList.toggle('dark', isDark)
}

// 强制亮色（登录/注册页默认亮色）
export function forceLight() {
  applyTheme(false)
}
