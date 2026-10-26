<template>
  <div class="suggestion-bar">
    <div class="suggestion-title">💡 常见问题</div>
    <div class="suggestion-list">
      <el-tag
        v-for="q in questions"
        :key="q"
        class="suggestion-item"
        effect="plain"
        @click="$emit('pick', q)"
      >
        {{ q }}
      </el-tag>
    </div>
  </div>
</template>

<script setup>
defineEmits(['pick'])

const questions = [
  '室外消火栓的保护半径是多少？',
  '给水管道的设计流速如何确定？',
  '室内消火栓系统的工作压力要求？',
  '建筑排水管道的坡度如何取值？',
  '排水管道的充满度有何规定？'
]
</script>

<style scoped>
.suggestion-bar {
  padding: 8px 0;
}
.suggestion-title {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}
.suggestion-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.suggestion-item {
  cursor: pointer;
  max-width: 260px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
