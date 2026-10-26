<template>
  <div class="knowledge-page">
    <el-card class="upload-card">
      <template #header>
        <span>上传规范文档（支持 txt / md / pdf / docx）</span>
      </template>
      <el-form label-width="90px">
        <el-form-item label="文件">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
            :file-list="fileList"
          >
            <el-button :icon="Upload">选择文件</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="规范名称">
          <el-input v-model="form.title" placeholder="如：室外给水设计标准" />
        </el-form-item>
        <el-form-item label="编号">
          <el-input v-model="form.code" placeholder="如：GB 50013" />
        </el-form-item>
        <el-form-item label="版本 / 年份">
          <el-input v-model="form.version" placeholder="如：2018" />
        </el-form-item>
        <el-form-item label="专业">
          <el-select v-model="form.category" placeholder="选择专业">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="uploading" @click="doUpload">上传并索引</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <span>规范列表</span>
      </template>
      <el-table :data="documents" v-loading="loading">
        <el-table-column prop="title" label="规范名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="code" label="编号" width="140" />
        <el-table-column prop="version" label="版本" width="90" />
        <el-table-column prop="category" label="专业" width="120" />
        <el-table-column prop="chunk_count" label="分片数" width="90" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tooltip v-if="row.status === 'failed'" :content="row.error" placement="top">
              <el-tag type="danger">失败</el-tag>
            </el-tooltip>
            <el-tag v-else :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewChunks(row)">查看分片</el-button>
            <el-button size="small" :loading="row.reindexing" @click="reindex(row)">重索引</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="chunkDialog" title="文档分片" width="70%">
      <div v-for="c in chunks" :key="c.id" class="chunk-item">
        <div class="chunk-meta">
          <el-tag size="small" type="info">{{ c.chapter || '—' }}</el-tag>
          <el-tag size="small" effect="plain">{{ c.clause || '—' }}</el-tag>
          <span>分片 #{{ c.chunk_index }}</span>
        </div>
        <div class="chunk-content">{{ c.content }}</div>
      </div>
      <el-empty v-if="!chunks.length" description="暂无分片" />
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import {
  deleteDocument,
  listChunks,
  listDocuments,
  reindexDocument,
  uploadDocument
} from '@/api/documents'
import { listCategories } from '@/api/categories'

const documents = ref([])
const categories = ref(['给水', '排水', '消防', '建筑给水排水', '其他'])
const loading = ref(false)
const uploading = ref(false)
const file = ref(null)
const fileList = ref([])
const form = reactive({ title: '', code: '', version: '', category: '其他' })
const chunks = ref([])
const chunkDialog = ref(false)

function onFileChange(uploadFile) {
  file.value = uploadFile.raw
}

function onFileRemove() {
  file.value = null
}

async function load() {
  loading.value = true
  try {
    const res = await listDocuments()
    documents.value = res.data || []
  } finally {
    loading.value = false
  }
}

async function doUpload() {
  if (!file.value || !form.title) {
    ElMessage.warning('请选择文件并填写规范名称')
    return
  }
  const fd = new FormData()
  fd.append('file', file.value)
  fd.append('title', form.title)
  fd.append('code', form.code)
  fd.append('version', form.version)
  fd.append('category', form.category)
  uploading.value = true
  try {
    await uploadDocument(fd)
    ElMessage.success('上传并索引成功')
    form.title = ''
    form.code = ''
    form.version = ''
    form.category = '其他'
    file.value = null
    fileList.value = []
    await load()
  } finally {
    uploading.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除《${row.title}》？将同时清除索引与文件。`, '提示', {
    type: 'warning'
  })
  await deleteDocument(row.id)
  ElMessage.success('已删除')
  await load()
}

async function reindex(row) {
  row.reindexing = true
  try {
    await reindexDocument(row.id)
    ElMessage.success('重新索引成功')
    await load()
  } finally {
    row.reindexing = false
  }
}

async function viewChunks(row) {
  const res = await listChunks(row.id)
  chunks.value = res.data || []
  chunkDialog.value = true
}

function statusType(s) {
  return { ready: 'success', indexing: 'warning', failed: 'danger', pending: 'info' }[s] || 'info'
}
function statusLabel(s) {
  return { ready: '已就绪', indexing: '索引中', failed: '失败', pending: '待处理' }[s] || s
}

onMounted(async () => {
  load()
  try {
    const res = await listCategories()
    categories.value = (res.data || []).map((c) => c.name)
  } catch {
    /* 忽略 */
  }
})
</script>

<style scoped>
.knowledge-page {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}
.upload-card {
  margin-bottom: 20px;
}
.chunk-item {
  padding: 10px 0;
  border-bottom: 1px dashed var(--el-border-color-light);
}
.chunk-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.chunk-content {
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--el-text-color-primary);
}
</style>
