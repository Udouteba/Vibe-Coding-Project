<template>
  <div class="scope-panel">
    <div class="scope-toolbar">
      <el-input v-model="searchText" placeholder="搜索规范名 / 编号" clearable :prefix-icon="Search" />
      <div class="scope-actions">
        <el-button size="small" @click="selectAll">全选</el-button>
        <el-button size="small" @click="clearAll">清空</el-button>
      </div>
    </div>

    <div class="scope-groups">
      <div v-for="group in grouped" :key="group.category" class="scope-group">
        <div class="group-head">
          <span class="group-name">{{ group.category }}</span>
          <span class="group-count">{{ group.count }} 本</span>
        </div>
        <div v-for="doc in group.docs" :key="doc.id" class="scope-doc" @click="toggle(doc.id)">
          <el-checkbox :model-value="selected.includes(doc.id)" @click.stop="toggle(doc.id)" />
          <span class="doc-title">{{ doc.title }}</span>
          <el-tag v-if="doc.code" size="small" type="info" class="doc-code">{{ doc.code }}</el-tag>
          <el-tag v-if="doc.version" size="small" effect="plain" class="doc-version">{{ doc.version }}</el-tag>
        </div>
      </div>
      <el-empty v-if="!grouped.length" description="无匹配规范" :image-size="50" />
    </div>

    <el-divider content-position="left">预设方案</el-divider>
    <div class="preset-save">
      <el-input v-model="presetName" placeholder="为当前选择命名并保存" size="small" />
      <el-button size="small" type="primary" :disabled="!presetName || !selected.length" @click="savePreset">
        保存
      </el-button>
    </div>
    <div class="preset-list">
      <div v-for="p in presets" :key="p.id" class="preset-item">
        <span class="preset-name" @click="applyPreset(p)">⭐ {{ p.name }}</span>
        <el-icon class="preset-del" @click="removePreset(p.id)"><Delete /></el-icon>
      </div>
      <div v-if="!presets.length" class="preset-empty">暂无预设</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Search } from '@element-plus/icons-vue'
import { createPreset, deletePreset, listPresets } from '@/api/presets'

const props = defineProps({
  documents: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:modelValue'])

const selected = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const searchText = ref('')
const presetName = ref('')
const presets = ref([])

const grouped = computed(() => {
  const kw = searchText.value.trim().toLowerCase()
  const ready = props.documents.filter((d) => d.status === 'ready')
  const filtered = ready.filter(
    (d) => !kw || d.title.toLowerCase().includes(kw) || (d.code || '').toLowerCase().includes(kw)
  )
  const map = new Map()
  for (const d of filtered) {
    if (!map.has(d.category)) map.set(d.category, [])
    map.get(d.category).push(d)
  }
  return Array.from(map.entries()).map(([category, docs]) => ({
    category,
    count: docs.length,
    docs
  }))
})

function toggle(id) {
  const set = new Set(selected.value)
  if (set.has(id)) set.delete(id)
  else set.add(id)
  selected.value = Array.from(set)
}

function selectAll() {
  selected.value = props.documents.filter((d) => d.status === 'ready').map((d) => d.id)
}

function clearAll() {
  selected.value = []
}

async function savePreset() {
  const res = await createPreset({ name: presetName.value, document_ids: selected.value })
  presets.value.unshift(res.data)
  presetName.value = ''
  ElMessage.success('预设已保存')
}

function applyPreset(p) {
  selected.value = p.document_ids || []
}

async function removePreset(id) {
  await deletePreset(id)
  presets.value = presets.value.filter((p) => p.id !== id)
}

onMounted(async () => {
  const res = await listPresets()
  presets.value = res.data || []
})
</script>

<style scoped>
.scope-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.scope-toolbar {
  margin-bottom: 8px;
}
.scope-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}
.scope-groups {
  flex: 1;
  overflow-y: auto;
}
.scope-group {
  margin-bottom: 12px;
}
.group-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.group-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-color-primary);
}
.group-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.scope-doc {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 6px;
  cursor: pointer;
}
.scope-doc:hover {
  background: var(--el-fill-color-light);
}
.doc-title {
  flex: 1;
  font-size: 13px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.doc-code {
  flex-shrink: 0;
}
.doc-version {
  flex-shrink: 0;
}
.preset-save {
  display: flex;
  gap: 8px;
}
.preset-list {
  margin-top: 8px;
  max-height: 140px;
  overflow-y: auto;
}
.preset-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  border-radius: 6px;
}
.preset-item:hover {
  background: var(--el-fill-color-light);
}
.preset-name {
  cursor: pointer;
  font-size: 13px;
  color: var(--el-text-color-primary);
}
.preset-del {
  cursor: pointer;
  color: var(--el-text-color-secondary);
}
.preset-del:hover {
  color: var(--el-color-danger);
}
.preset-empty {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  padding: 4px 8px;
}
</style>
