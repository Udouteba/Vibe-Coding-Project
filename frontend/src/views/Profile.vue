<template>
  <div class="profile-page">
    <el-card class="profile-card">
      <template #header>
        <span>个人信息</span>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ user?.username }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag :type="user?.role === 'admin' ? 'danger' : 'info'">
            {{ user?.role === 'admin' ? '管理员' : '普通用户' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider>修改密码</el-divider>
      <el-form :model="form" label-width="90px" class="pwd-form">
        <el-form-item label="原密码">
          <el-input v-model="form.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="form.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="form.confirm" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">确认修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { changePassword } from '@/api/auth'
import { getUserInfo, logout } from '@/utils/auth'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = getUserInfo()
const loading = ref(false)
const form = reactive({ old_password: '', new_password: '', confirm: '' })

async function submit() {
  if (!form.old_password || !form.new_password) {
    ElMessage.warning('请填写完整')
    return
  }
  if (form.new_password !== form.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  loading.value = true
  try {
    await changePassword({ old_password: form.old_password, new_password: form.new_password })
    ElMessage.success('密码修改成功，请重新登录')
    logout()
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-page {
  padding: 20px;
  height: 100%;
  overflow: auto;
}
.profile-card {
  max-width: 520px;
}
.pwd-form {
  max-width: 420px;
}
</style>
