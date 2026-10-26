<template>
  <div class="chat-page">
    <div class="chat-side">
      <ConversationSidebar
        :conversations="conversations"
        :active-id="activeConvId"
        @select="selectConversation"
        @new="newConversation"
        @rename="renameConversation"
        @pin="pinConversation"
        @archive="archiveConversation"
        @delete="deleteConversation"
      />
    </div>

    <div class="chat-main">
      <div class="chat-topbar">
        <el-button @click="scopeDrawer = true">
          <el-icon><Filter /></el-icon>
          <span>检索范围（{{ scopeLabel }}）</span>
        </el-button>
        <div class="scope-tags">
          <el-tag v-for="id in scopeIds" :key="id" size="small" closable @close="removeScope(id)">
            {{ docTitle(id) }}
          </el-tag>
          <el-tag v-if="!scopeIds.length" size="small" type="info" effect="plain">全部规范</el-tag>
        </div>
      </div>

      <div ref="msgRef" class="chat-messages">
        <el-empty v-if="!messages.length" description="选择一个会话或开始新的提问" />
        <div v-for="(m, i) in messages" :key="i" class="msg-row" :class="m.role">
          <div v-if="m.role === 'user'" class="user-bubble">{{ m.content }}</div>
          <div v-else class="assistant-block">
            <div v-if="m.streaming && !m.content" class="typing">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
              <span class="typing-text">检索中…</span>
            </div>
            <AnswerView v-else :message="m" />
            <div v-if="m.error" class="err-text">⚠️ {{ m.error }}</div>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <SuggestionBar @pick="pickSuggestion" />
        <div class="input-row">
          <el-input
            v-model="input"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="输入你的问题，例如：室外消火栓的保护半径是多少？"
            @keydown.enter.exact.prevent="send"
          />
          <el-button
            type="primary"
            class="send-btn"
            :loading="streaming"
            :disabled="!input.trim()"
            @click="send"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>

    <el-drawer v-model="scopeDrawer" title="选择检索范围" size="380px">
      <ScopePanel v-model="scopeIds" :documents="documents" />
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteConversation as deleteConversationApi,
  listConversations,
  listMessages,
  updateConversation
} from '@/api/conversations'
import { listDocuments } from '@/api/documents'
import { streamChat } from '@/api/chat'
import AnswerView from '@/components/AnswerView.vue'
import ConversationSidebar from '@/components/ConversationSidebar.vue'
import ScopePanel from '@/components/ScopePanel.vue'
import SuggestionBar from '@/components/SuggestionBar.vue'

const conversations = ref([])
const activeConvId = ref(null)
const messages = ref([])
const documents = ref([])
const scopeIds = ref([])
const input = ref('')
const streaming = ref(false)
const scopeDrawer = ref(false)
const msgRef = ref(null)

const scopeLabel = computed(() => (scopeIds.value.length ? `${scopeIds.value.length} 本` : '全部'))

function docTitle(id) {
  return documents.value.find((d) => d.id === id)?.title || `#${id}`
}

async function loadDocuments() {
  const res = await listDocuments()
  documents.value = res.data || []
}

async function loadConversations() {
  const res = await listConversations()
  conversations.value = res.data || []
}

async function selectConversation(id) {
  activeConvId.value = id
  const res = await listMessages(id)
  messages.value = res.data || []
  scrollBottom()
}

function newConversation() {
  activeConvId.value = null
  messages.value = []
  scopeIds.value = []
}

async function renameConversation(id, title) {
  await updateConversation(id, { title })
  await loadConversations()
}

async function pinConversation(id, pinned) {
  await updateConversation(id, { is_pinned: pinned })
  await loadConversations()
}

async function archiveConversation(id) {
  await updateConversation(id, { is_archived: true })
  if (activeConvId.value === id) newConversation()
  await loadConversations()
}

async function deleteConversation(id) {
  await ElMessageBox.confirm('确定删除该会话？删除后不可恢复。', '提示', { type: 'warning' })
  await deleteConversationApi(id)
  if (activeConvId.value === id) newConversation()
  await loadConversations()
}

function removeScope(id) {
  scopeIds.value = scopeIds.value.filter((x) => x !== id)
}

function scrollBottom() {
  nextTick(() => {
    if (msgRef.value) msgRef.value.scrollTop = msgRef.value.scrollHeight
  })
}

function pickSuggestion(q) {
  input.value = q
  send()
}

async function send() {
  const text = input.value.trim()
  if (!text || streaming.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  const assistant = {
    role: 'assistant',
    content: '',
    citations: [],
    low_confidence: false,
    streaming: true
  }
  messages.value.push(assistant)
  streaming.value = true
  scrollBottom()
  try {
    await streamChat({
      conversationId: activeConvId.value,
      message: text,
      documentIds: scopeIds.value,
      onEvent: (ev) => {
        if (ev.event === 'token') {
          assistant.content += ev.data.content
          scrollBottom()
        } else if (ev.event === 'tool_start') {
          assistant.status = '检索中…'
        } else if (ev.event === 'tool_end') {
          assistant.status = '生成中…'
        } else if (ev.event === 'citations') {
          assistant.citations = ev.data.items
        } else if (ev.event === 'done') {
          assistant.low_confidence = ev.data.low_confidence
          assistant.id = ev.data.message_id
          if (!activeConvId.value) activeConvId.value = ev.data.conversation_id
        } else if (ev.event === 'error') {
          assistant.error = ev.data.message
          if (!activeConvId.value) activeConvId.value = ev.data.conversation_id
        }
      }
    })
  } catch (e) {
    assistant.error = e.message
  } finally {
    assistant.streaming = false
    streaming.value = false
    await loadConversations()
    scrollBottom()
  }
}

onMounted(async () => {
  await loadDocuments()
  await loadConversations()
  if (conversations.value.length) {
    await selectConversation(conversations.value[0].id)
  }
})
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100%;
}
.chat-side {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}
.chat-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.chat-topbar {
  padding: 10px 16px;
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.scope-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.msg-row {
  margin-bottom: 20px;
  display: flex;
}
.msg-row.user {
  justify-content: flex-end;
}
.msg-row.assistant {
  justify-content: flex-start;
}
.user-bubble {
  max-width: 70%;
  padding: 10px 14px;
  background: var(--el-color-primary);
  color: #fff;
  border-radius: 12px 12px 2px 12px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}
.assistant-block {
  max-width: 85%;
  min-width: 0;
  width: 85%;
}
.typing {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.typing .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--el-color-primary);
  animation: blink 1.2s infinite;
}
.typing .dot:nth-child(2) {
  animation-delay: 0.2s;
}
.typing .dot:nth-child(3) {
  animation-delay: 0.4s;
}
.typing-text {
  margin-left: 6px;
}
@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.2;
  }
  40% {
    opacity: 1;
  }
}
.err-text {
  margin-top: 6px;
  color: var(--el-color-danger);
  font-size: 13px;
}
.chat-input {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}
.input-row {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}
.send-btn {
  height: 54px;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .chat-side {
    display: none;
  }
  .assistant-block {
    width: 100%;
    max-width: 100%;
  }
}
</style>
