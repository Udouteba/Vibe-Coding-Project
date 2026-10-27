// 用户名与密码规则校验（与后端 utils/validators.py 保持一致）
// 返回错误信息字符串，合法时返回 null（空值返回 null，由调用方处理必填）

export function usernameError(v) {
  if (!v) return null
  if (v.length < 5 || v.length > 20) return '用户名长度需为 5~20 个字符'
  if (!/^[A-Za-z0-9_]+$/.test(v)) return '用户名只能包含英文字母、数字、下划线'
  return null
}

export function passwordError(v) {
  if (!v) return null
  if (v.length < 8) return '密码至少 8 位'
  if (!/^[A-Za-z0-9_]+$/.test(v)) return '密码只能包含英文字母、数字、下划线'
  let kinds = 0
  if (/[A-Z]/.test(v)) kinds++
  if (/[a-z]/.test(v)) kinds++
  if (/[0-9]/.test(v)) kinds++
  if (kinds < 2) return '密码需包含大写字母、小写字母、数字中的至少两类'
  return null
}
