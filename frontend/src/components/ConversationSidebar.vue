<template>
  <div class="conv-sidebar">
    <div class="conv-header">
      <el-button type="primary" class="new-btn" @click="$emit('new')">
        <el-icon><Plus /></el-icon>
        <span>新建会话</span>
      </el-button>
    </div>
    <div class="conv-list">
      <div
        v-for="c in conversations"
        :key="c.id"
        class="conv-item"
        :class="{ active: c.id === activeId }"
        @click="$emit('select', c.id)"
      >
        <div class="conv-row">
          <el-icon v-if="c.is_pinned" class="pin-icon"><Top /></el-icon>
          <span class="conv-title">{{ c.title }}</span>
          <el-dropdown trigger="click" @command="(cmd) => onCommand(cmd, c)" @click.stop>
            <el-icon class="more-icon"><MoreFilled /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename">重命名</el-dropdown-item>
                <el-dropdown-item command="pin">{{ c.is_pinned ? '取消置顶' : '置顶' }}</el-dropdown-item>
                <el-dropdown-item command="archive">归档</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div class="conv-preview">{{ c.last_message || '暂无消息' }}</div>
      </div>
      <el-empty v-if="!conversations.length" description="暂无会话" :image-size="60" />
    </div>
  </div>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'

defineProps({
  conversations: { type: Array, default: () => [] },
  activeId: { type: Number, default: null }
})

const emit = defineEmits(['select', 'new', 'rename', 'pin', 'archive', 'delete'])

async function onCommand(cmd, c) {
  if (cmd === 'rename') {
    try {
      const { value } = await ElMessageBox.prompt('请输入会话名称', '重命名', {
        inputValue: c.title,
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      })
      if (value) emit('rename', c.id, value)
    } catch {
      /* 用户取消 */
    }
  } else if (cmd === 'pin') {
    emit('pin', c.id, !c.is_pinned)
  } else if (cmd === 'archive') {
    emit('archive', c.id)
  } else if (cmd === 'delete') {
    emit('delete', c.id)
  }
}
</script>

<style scoped>
.conv-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.conv-header {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-light);
}
.new-btn {
  width: 100%;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.conv-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.15s;
}
.conv-item:hover {
  background: var(--el-fill-color-light);
}
.conv-item.active {
  background: var(--el-color-primary-light-9);
}
.conv-row {
  display: flex;
  align-items: center;
  gap: 4px;
}
.pin-icon {
  color: var(--el-color-warning);
  font-size: 14px;
}
.conv-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--el-text-color-primary);
}
.more-icon {
  color: var(--el-text-color-secondary);
  visibility: hidden;
}
.conv-item:hover .more-icon {
  visibility: visible;
}
.conv-preview {
  margin-top: 3px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
