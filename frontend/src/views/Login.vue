<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="auth-title">💧 给排水智库 · 登录</h2>
      <el-form @submit.prevent="submit">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            show-password
            :prefix-icon="Lock"
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-button type="primary" class="auth-btn" :loading="loading" @click="submit">
          登录
        </el-button>
        <div class="auth-footer">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
      </el-form>
      <el-alert
        class="auth-hint"
        type="info"
        :closable="false"
        title="演示账号：admin / admin（管理员）、aaa / 123（学生）"
      />
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { login } from '@/api/auth'
import { setToken, setUserInfo } from '@/utils/auth'

const router = useRouter()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await login(form)
    setToken(res.data.token)
    setUserInfo(res.data.user)
    ElMessage.success('登录成功')
    router.push('/chat')
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
.auth-hint {
  margin-top: 16px;
}
</style>
