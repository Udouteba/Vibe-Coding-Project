import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Knowledge from '@/views/Knowledge.vue'
import { listChunks } from '@/api/documents'

const { mockDocs, mockChunks } = vi.hoisted(() => ({
  mockDocs: [
    {
      id: 1,
      title: '室外给水设计标准',
      code: 'GB 50013',
      version: '2018',
      category: '给水',
      chunk_count: 1,
      status: 'ready'
    }
  ],
  mockChunks: [
    {
      id: 10,
      chapter: '第三章',
      section: '3.1',
      clause: '3.2.5',
      page: 5,
      chunk_index: 0,
      content: '条文内容'
    }
  ]
}))

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  ElMessageBox: { confirm: vi.fn().mockResolvedValue(true) }
}))

vi.mock('@element-plus/icons-vue', () => ({
  Upload: { name: 'Upload', render: () => null }
}))

vi.mock('@/api/documents', () => ({
  listDocuments: vi.fn().mockResolvedValue({ data: mockDocs }),
  listChunks: vi.fn().mockResolvedValue({ data: mockChunks }),
  uploadDocument: vi.fn().mockResolvedValue({}),
  deleteDocument: vi.fn().mockResolvedValue({}),
  reindexDocument: vi.fn().mockResolvedValue({})
}))

vi.mock('@/api/categories', () => ({
  listCategories: vi.fn().mockResolvedValue({ data: [] })
}))

// el-button 渲染为原生 button，透传 @click 以便触发 viewChunks
const ElButton = {
  name: 'ElButton',
  inheritAttrs: false,
  template: '<button v-bind="$attrs"><slot /></button>'
}
// el-table-column 把 scoped slot 渲染出来，row 取 mockDocs[0]
const ElTableColumn = {
  name: 'ElTableColumn',
  props: ['prop', 'label', 'width', 'minWidth', 'fixed', 'showOverflowTooltip'],
  setup(_, { slots }) {
    return () => (slots.default ? slots.default({ row: mockDocs[0] }) : null)
  }
}

const stubs = {
  ElButton,
  ElTableColumn,
  ElTable: { template: '<div class="el-table"><slot /></div>' },
  ElDialog: { template: '<div class="el-dialog"><slot /></div>' },
  ElCard: true,
  ElForm: true,
  ElFormItem: true,
  ElUpload: true,
  ElInput: true,
  ElSelect: true,
  ElOption: true,
  ElTooltip: true,
  ElTag: true,
  ElEmpty: true
}

const globalOptions = {
  stubs,
  directives: { loading: { mounted() {} } },
  renderStubDefaultSlot: true
}

beforeEach(() => {
  vi.clearAllMocks()
})

async function openChunkDialog() {
  const wrapper = mount(Knowledge, { global: globalOptions })
  await flushPromises()
  const btn = wrapper.findAll('button').find((b) => b.text().includes('查看分片'))
  expect(btn).toBeTruthy()
  await btn.trigger('click')
  await flushPromises()
  return wrapper
}

describe('Knowledge 分片查看', () => {
  it('分片弹窗显示 chapter/section/clause/page', async () => {
    const wrapper = await openChunkDialog()

    expect(listChunks).toHaveBeenCalledWith(1)

    const text = wrapper.find('.el-dialog').text()
    expect(text).toContain('第三章') // chapter
    expect(text).toContain('3.1') // section
    expect(text).toContain('3.2.5') // clause
    expect(text).toContain('P.5') // page
    expect(text).toContain('条文内容')
  })

  it('状态列渲染就绪文案', async () => {
    const wrapper = await openChunkDialog()
    expect(wrapper.text()).toContain('已就绪')
  })

  it('分片缺少 section/page 时显示占位符且不显示 P.', async () => {
    listChunks.mockResolvedValueOnce({
      data: [{ id: 11, chapter: '', section: '', clause: '', page: null, chunk_index: 0, content: '内容' }]
    })
    const wrapper = await openChunkDialog()

    const text = wrapper.find('.el-dialog').text()
    expect(text).toContain('—')
    expect(text).not.toContain('P.')
  })
})
