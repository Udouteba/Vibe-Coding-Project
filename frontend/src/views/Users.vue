<template>
  <div class="users-page">
    <el-card>
      <template #header>
        <div class="users-header">
          <span>用户管理</span>
          <el-button type="primary" :icon="Plus" @click="openCreate">新建用户</el-button>
        </div>
      </template>
      <el-table :data="users" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column label="角色" width="140">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="200">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :disabled="row.id === currentUserId" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :disabled="row.role === 'admin'" @click="remove(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialog" :title="editing ? '编辑用户' : '新建用户'" width="420px">
      <el-form label-width="80px">
        <el-form-item label="用户名" :error="usernameErr">
          <el-input
            v-model="form.username"
            :disabled="editing"
            placeholder="5-20 位字母/数字/下划线"
            @blur="onBlurUsername"
            @input="usernameErr = ''"
          />
        </el-form-item>
        <el-form-item label="密码" :error="passwordErr">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="editing ? '留空则不修改' : '至少 8 位，含大小写/数字两类'"
            @blur="onBlurPassword"
            @input="passwordErr = ''"
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role">
            <el-option label="普通用户" value="student" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createUser, deleteUser, listUsers, updateUser } from '@/api/users'
import { getUserInfo } from '@/utils/auth'
import { passwordError, usernameError } from '@/utils/validators'

const users = ref([])
const loading = ref(false)
const dialog = ref(false)
const editing = ref(false)
const editId = ref(null)
const form = reactive({ username: '', password: '', role: 'student' })
const usernameErr = ref('')
const passwordErr = ref('')
const currentUserId = getUserInfo()?.id

async function load() {
  loading.value = true
  try {
    const res = await listUsers()
    users.value = res.data || []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = false
  editId.value = null
  form.username = ''
  form.password = ''
  form.role = 'student'
  dialog.value = true
}

function openEdit(row) {
  editing.value = true
  editId.value = row.id
  form.username = row.username
  form.password = ''
  form.role = row.role
  dialog.value = true
}

function onBlurUsername() {
  if (editing.value) return
  usernameErr.value = usernameError(form.username) || ''
}

function onBlurPassword() {
  passwordErr.value = passwordError(form.password) || ''
}

async function save() {
  if (editing.value) {
    if (form.password) {
      const msg = passwordError(form.password)
      if (msg) {
        ElMessage.warning(msg)
        return
      }
    }
    const data = { role: form.role }
    if (form.password) data.password = form.password
    await updateUser(editId.value, data)
  } else {
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
    await createUser({ username: form.username, password: form.password, role: form.role })
  }
  ElMessage.success('保存成功')
  dialog.value = false
  await load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除用户「${row.username}」？`, '提示', { type: 'warning' })
  await deleteUser(row.id)
  ElMessage.success('已删除')
  await load()
}

function formatTime(t) {
  return t ? new Date(t).toLocaleString() : '-'
}

onMounted(load)
</script>

<style scoped>
.users-page {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}
.users-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
