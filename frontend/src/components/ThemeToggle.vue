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

const isDark = ref(false)

function apply() {
  document.documentElement.classList.toggle('dark', isDark.value)
}

function toggle() {
  isDark.value = !isDark.value
  apply()
  localStorage.setItem('drainage_theme', isDark.value ? 'dark' : 'light')
}

onMounted(() => {
  const saved = localStorage.getItem('drainage_theme')
  if (saved === 'dark') {
    isDark.value = true
  } else if (saved === 'light') {
    isDark.value = false
  } else {
    isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  apply()
})
</script>
