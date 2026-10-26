<template>
  <div class="source-collapse">
    <div class="source-head">📚 引用来源（{{ citations.length }}）</div>
    <el-collapse v-model="openItems">
      <el-collapse-item
        v-for="(item, i) in citations"
        :key="i"
        :name="i"
      >
        <template #title>
          <div class="source-title" :id="'cite-src-' + (i + 1)">
            <span class="source-idx" :class="{ highlight: highlightIdx === i + 1 }">[{{ i + 1 }}]</span>
            <span class="source-meta">{{ formatCitation(item) }}</span>
            <el-tag v-if="item.version" size="small" effect="plain">{{ item.version }}版</el-tag>
          </div>
        </template>
        <div class="source-body">
          <p class="source-content">{{ item.content }}</p>
          <div class="source-actions">
            <el-button size="small" :icon="CopyDocument" @click="copy(item)">复制引用格式</el-button>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument } from '@element-plus/icons-vue'
import { copyText, formatCitation } from '@/utils/citation'

const props = defineProps({
  citations: { type: Array, default: () => [] },
  highlightIdx: { type: Number, default: 0 }
})

const openItems = ref([])

watch(
  () => props.highlightIdx,
  (idx) => {
    if (idx > 0) {
      openItems.value = [idx - 1]
      setTimeout(() => {
        document.getElementById('cite-src-' + idx)?.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        })
      }, 100)
    }
  }
)

async function copy(item) {
  await copyText(formatCitation(item))
  ElMessage.success('已复制引用格式')
}
</script>

<style scoped>
.source-collapse {
  margin-top: 12px;
}
.source-head {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--el-text-color-primary);
}
.source-title {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.source-idx {
  color: var(--el-color-primary);
  font-weight: 600;
  flex-shrink: 0;
}
.source-idx.highlight {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 2px;
  border-radius: 4px;
}
.source-meta {
  flex: 1;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.source-body {
  padding: 4px 0;
}
.source-content {
  margin: 0 0 8px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--el-text-color-regular);
  white-space: pre-wrap;
  word-break: break-word;
}
.source-actions {
  text-align: right;
}
</style>
