<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="auth-title">💧 给排水智库 · 注册</h2>
      <el-form @submit.prevent="submit">
        <el-form-item :error="usernameErr">
          <el-input
            v-model="form.username"
            placeholder="用户名（5-20 位字母/数字/下划线）"
            :prefix-icon="User"
            @blur="onBlurUsername"
            @input="usernameErr = ''"
          />
        </el-form-item>
        <el-form-item :error="passwordErr">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码（至少 8 位，含大小写/数字两类）"
            show-password
            :prefix-icon="Lock"
            @blur="onBlurPassword"
            @input="passwordErr = ''"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.confirm"
            type="password"
            placeholder="确认密码"
            show-password
            :prefix-icon="Lock"
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-button type="primary" class="auth-btn" :loading="loading" @click="submit">
          注册
        </el-button>
        <div class="auth-footer">
          <span>已有账号？</span>
          <router-link to="/login">去登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { register } from '@/api/auth'
import { forceLight } from '@/utils/theme'
import { passwordError, usernameError } from '@/utils/validators'

const router = useRouter()
const loading = ref(false)
const form = reactive({ username: '', password: '', confirm: '' })
const usernameErr = ref('')
const passwordErr = ref('')

onMounted(forceLight)

function onBlurUsername() {
  usernameErr.value = usernameError(form.username) || ''
}

function onBlurPassword() {
  passwordErr.value = passwordError(form.password) || ''
}

async function submit() {
  if (!form.username) {
    ElMessage.warning('请输入用户名')
    return
  }
  const usernameMsg = usernameError(form.username)
  if (usernameMsg) {
    ElMessage.warning(usernameMsg)
    return
  }
  if (!form.password) {
    ElMessage.warning('请输入密码')
    return
  }
  const passwordMsg = passwordError(form.password)
  if (passwordMsg) {
    ElMessage.warning(passwordMsg)
    return
  }
  if (form.password !== form.confirm) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    await register({ username: form.username, password: form.password })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e3a8a 0%, #0ea5e9 100%);
}
.auth-card {
  width: 380px;
  padding: 8px 16px;
}
.auth-title {
  text-align: center;
  margin-bottom: 20px;
  color: var(--el-text-color-primary);
}
.auth-btn {
  width: 100%;
  margin-top: 4px;
}
.auth-footer {
  margin-top: 14px;
  text-align: center;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}
</style>
