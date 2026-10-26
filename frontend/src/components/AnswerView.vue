<template>
  <div class="answer-view">
    <el-alert
      v-if="message.low_confidence"
      class="conf-alert"
      type="warning"
      :closable="false"
      title="⚠️ 检索到的规范内容可能不足以支撑完整回答，以下内容仅供参考。"
    />

    <div
      class="answer-markdown"
      :class="{ 'is-streaming': message.streaming }"
      v-html="renderedHtml"
      @click="onClick"
      @mouseover="onMouseover"
      @mouseout="onMouseout"
    ></div>

    <SourceCollapse
      v-if="!message.streaming && citations.length"
      :citations="citations"
      :highlight-idx="highlightIdx"
    />

    <Teleport to="body">
      <div v-show="popover.show" class="cite-popover" :style="popover.style">
        <div class="cite-popover-head">{{ popover.title }}</div>
        <div class="cite-popover-body">{{ popover.content }}</div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { ElMessage } from 'element-plus'
import SourceCollapse from './SourceCollapse.vue'
import { copyText, formatCitation } from '@/utils/citation'

const props = defineProps({
  message: { type: Object, required: true }
})

const citations = computed(() => props.message.citations || [])
const highlightIdx = ref(0)
const popover = reactive({ show: false, title: '', content: '', style: {} })

const COPY_SVG =
  '<svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
}

const renderedHtml = computed(() => {
  const text = props.message.content || ''
  // 流式输出期间用纯文本，避免半成品 markdown 反复解析
  if (props.message.streaming) {
    return escapeHtml(text)
  }
  const protectedText = text.replace(/\[(\d{1,2})\]/g, (m, n) => {
    const idx = parseInt(n, 10)
    if (idx >= 1 && idx <= citations.value.length) return `⟦CITE:${idx}⟧`
    return m
  })
  const raw = marked.parse(protectedText, { breaks: true })
  const clean = DOMPurify.sanitize(raw)
  return clean.replace(/⟦CITE:(\d+)⟧/g, (m, n) => {
    return `<span class="cite-chip" data-idx="${n}">[${n}]${COPY_SVG}</span>`
  })
})

function locate(idx) {
  highlightIdx.value = idx
  document
    .querySelectorAll('.cite-chip.highlight')
    .forEach((el) => el.classList.remove('highlight'))
  const chip = document.querySelector(`.cite-chip[data-idx="${idx}"]`)
  chip?.classList.add('highlight')
}

function onClick(e) {
  const chip = e.target.closest('.cite-chip')
  if (!chip) return
  const idx = parseInt(chip.dataset.idx, 10)
  if (e.target.closest('.copy-icon')) {
    const item = citations.value[idx - 1]
    if (item) {
      copyText(formatCitation(item))
      ElMessage.success('已复制引用格式')
    }
  } else {
    locate(idx)
  }
}

function onMouseover(e) {
  const chip = e.target.closest('.cite-chip')
  if (!chip) return
  const idx = parseInt(chip.dataset.idx, 10)
  const item = citations.value[idx - 1]
  if (!item) return
  popover.title = formatCitation(item)
  popover.content = item.content
  const rect = chip.getBoundingClientRect()
  popover.style = { left: `${rect.left}px`, top: `${rect.bottom + 8}px` }
  popover.show = true
}

function onMouseout(e) {
  if (e.target.closest('.cite-chip')) popover.show = false
}
</script>

<style scoped>
.answer-view {
  position: relative;
}
.conf-alert {
  margin-bottom: 8px;
}
.answer-markdown.is-streaming {
  white-space: pre-wrap;
}
</style>
