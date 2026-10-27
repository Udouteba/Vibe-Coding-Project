import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AnswerView from '@/components/AnswerView.vue'

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }
}))

const ElAlertStub = {
  props: ['title'],
  template: '<div class="el-alert">{{ title }}</div>'
}

const globalOptions = {
  stubs: { ElAlert: ElAlertStub, SourceCollapse: true }
}

describe('AnswerView', () => {
  it('引用标记渲染为 cite-chip', () => {
    const wrapper = mount(AnswerView, {
      props: {
        message: {
          content: '规范要求[1]',
          citations: [
            { title: '规范', code: 'GB', version: '2019', chapter: '第一章', clause: '1.1', content: '条文' }
          ]
        }
      },
      global: globalOptions
    })
    const chip = wrapper.find('.cite-chip')
    expect(chip.exists()).toBe(true)
    expect(chip.attributes('data-idx')).toBe('1')
  })

  it('streaming 时按纯文本转义，不产生 script 元素', () => {
    const wrapper = mount(AnswerView, {
      props: { message: { content: '<script>alert(1)</script>', streaming: true, citations: [] } },
      global: globalOptions
    })
    expect(wrapper.find('.answer-markdown script').exists()).toBe(false)
    expect(wrapper.find('.answer-markdown').text()).toBe('<script>alert(1)</script>')
  })

  it('low_confidence 显示警告', () => {
    const wrapper = mount(AnswerView, {
      props: { message: { content: '答', low_confidence: true, citations: [] } },
      global: globalOptions
    })
    expect(wrapper.find('.el-alert').text()).toContain('检索到的规范内容可能不足以支撑完整回答')
  })

  it('普通回答渲染内容', () => {
    const wrapper = mount(AnswerView, {
      props: { message: { content: '普通回答', citations: [] } },
      global: globalOptions
    })
    expect(wrapper.find('.answer-markdown').text()).toContain('普通回答')
  })
})
