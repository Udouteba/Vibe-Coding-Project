<template>
  <el-tooltip :content="isDark ? '切换到浅色模式' : '切换到暗色模式'" placement="bottom">
    <el-button circle text @click="toggle">
      <el-icon v-if="!isDark"><Moon /></el-icon>
      <el-icon v-else><Sunny /></el-icon>
    </el-button>
  </el-tooltip>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { applyTheme } from '@/utils/theme'
import { getUserInfo, setUserInfo } from '@/utils/auth'
import { updateTheme } from '@/api/auth'

const isDark = ref(false)

function toggle() {
  isDark.value = !isDark.value
  applyTheme(isDark.value)
  const theme = isDark.value ? 'dark' : 'light'
  const user = getUserInfo()
  if (user) {
    user.theme = theme
    setUserInfo(user)
  }
  updateTheme(theme).catch(() => {})
}

onMounted(() => {
  isDark.value = getUserInfo()?.theme === 'dark'
  applyTheme(isDark.value)
})
</script>
