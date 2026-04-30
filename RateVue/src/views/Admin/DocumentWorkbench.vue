        await rejectDocument(this.rejectForm.documentId)
        const response = await generateVectors(this.selectedDocument.doc_id || this.selectedDocument.id, {
        const res = await previewChunks(this.selectedDocument.doc_id || this.selectedDocument.id, {
        ElMessage.warning('未找到文件路径信息，请先查看文档详情获取路径')
      const filePath = this.selectedDocument.file_path || ''
    openFile() {
        this.documentContent = res.content || res.data?.content || doc.content || ''
        if (res.file_path) {
          this.selectedDocument.file_path = res.file_path
        this.documentList = res.data?.items || []
        this.total = res.data?.total || this.documentList.length
  rejectDocument,
  previewChunks
<template>
  <div class="doc-workbench">
    <h2>文档审核工作台</h2>

    <el-card class="list-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>待审核文档</span>
          <el-button type="primary" size="small" @click="loadDocuments" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新列表
          </el-button>
        </div>
      </template>

      <el-table :data="documentList" v-loading="loading" border stripe>
        <el-table-column prop="doc_id" label="文档ID" width="100" align="center" />
        <el-table-column prop="doc_name" label="文档标题" show-overflow-tooltip />
        <el-table-column prop="uploader_type" label="来源" width="100" align="center" />
        <el-table-column prop="created_at" label="上传时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="scope">
            <el-button size="small" type="info" plain @click="viewDetail(scope.row)">查看详情</el-button>
            <el-button size="small" type="danger" plain @click="rejectDocument(scope.row)">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container" v-if="total > pageSize">
        <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="loadDocuments"
            @current-change="loadDocuments"
        />
      </div>
    </el-card>

    <el-card v-if="selectedDocument" class="detail-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span><el-icon><Document /></el-icon> 文档详情 - {{ selectedDocument.doc_name }}</span>
          <el-tag :type="selectedDocument.uploader_type === 'admin' ? 'success' : 'info'" size="small">
            {{ selectedDocument.uploader_type }}
          </el-tag>
        </div>
      </template>

      <div class="three-column-layout">
        <div class="column config-column">
          <h4>拆分配置</h4>
          <el-form :model="processParams" label-position="top" size="default">
            <el-form-item label="块大小 (chunk_size)">
              <el-slider v-model.number="processParams.chunk_size" :min="100" :max="1000" :step="50" show-input />
            </el-form-item>
            <el-form-item label="重叠量 (overlap)">
              <el-slider
                  v-model.number="processParams.chunk_overlap"
                  :min="0"
                  :max="processParams.chunk_size - 20"
                  :step="10"
                  show-input
                  :disabled="processParams.chunk_size <= 50"
              />
            </el-form-item>
          </el-form>
        </div>

        <div class="column preview-column">
          <h4>拆分预览 <span v-if="chunks.length" class="badge">{{ chunks.length }}块</span></h4>
          <div class="preview-content" v-loading="processingChunks">
            <el-scrollbar max-height="320px" v-if="chunks.length">
              <div v-for="(chunk, idx) in chunks" :key="idx" class="chunk-item">
                <div class="chunk-header">
                  <span class="chunk-index">#{{ idx + 1 }}</span>
                  <span class="chunk-len">{{ chunk.length || (chunk.content?.length || 0) }} 字符</span>
                </div>
                <div class="chunk-text">{{ chunk.content || chunk }}</div>
              </div>
            </el-scrollbar>
            <el-empty v-else description="点击「拆分预览」生成块" :image-size="80" />
          </div>
        </div>

        <div class="column vector-column">
          <h4>向量预览 <span v-if="vectorPreview.length" class="badge">{{ vectorPreview.length }}项</span></h4>
          <div class="preview-content" v-loading="processingVectors">
            <el-scrollbar max-height="320px" v-if="vectorPreview.length">
              <div v-for="(vec, idx) in vectorPreview.slice(0, 20)" :key="idx" class="vector-item">
                <div class="vector-header">
                  <span class="vector-index">块 {{ idx + 1 }}</span>
                  <span class="vector-dim">维度 {{ vec.length }}</span>
                </div>
                <div class="vector-values">
                  [ {{ vec.slice(0, 6).map(v => v.toFixed(3)).join(', ') }}{{ vec.length > 6 ? '...' : '' }} ]
                </div>
              </div>
              <div v-if="vectorPreview.length > 20" class="more-hint">仅展示前20项</div>
            </el-scrollbar>
            <el-empty v-else description="点击「向量预览」生成向量" :image-size="80" />
          </div>
        </div>
      </div>

      <div class="action-bar">
        <el-button-group>
          <el-button @click="openFile" :disabled="!selectedDocument" size="large">
            <el-icon><FolderOpened /></el-icon> 打开文件
          </el-button>
          <el-button @click="previewChunks" :loading="processingChunks" size="large" :disabled="!selectedDocument">
            <el-icon><View /></el-icon> 拆分预览
          </el-button>
          <el-button @click="generateVectors" :loading="processingVectors" size="large" :disabled="!chunks.length">
            <el-icon><DataLine /></el-icon> 向量预览
          </el-button>
          <el-button type="success" @click="approveAndParseDocument" :loading="processing" size="large">
            <el-icon><Check /></el-icon> 审核入库
          </el-button>
        </el-button-group>
      </div>
    </el-card>

    <el-empty v-else description="请从左侧列表选择一份文档开始处理" :image-size="120" class="empty-detail" />

    <el-dialog v-model="rejectDialogVisible" title="驳回文档" width="400px">
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="驳回原因">
          <el-input v-model="rejectForm.reason" type="textarea" :rows="3" placeholder="请输入驳回原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmReject" :loading="processing">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Document, FolderOpened, View, DataLine, Check } from '@element-plus/icons-vue'
import {
  getPendingDocuments,
  approveDocument,
  generateVectors,
  getDocumentDetail,
  rejectDocument,
  previewChunks, previewDocument
} from '@/api/documentWorkbench'

export default {
  name: 'DocumentWorkbench',
  components: { Refresh, Document, FolderOpened, View, DataLine, Check },

  data() {
    return {
      documentList: [],
      total: 0,
      currentPage: 1,
      pageSize: 20,
      loading: false,

      selectedDocument: null,
      documentContent: '',

      processParams: {
        chunk_size: 500,
        chunk_overlap: 50
      },
      chunks: [],
      vectorPreview: [],

      processingChunks: false,
      processingVectors: false,
      processing: false,

      rejectDialogVisible: false,
      rejectForm: {
        documentId: null,
        reason: ''
      }
    }
  },

  mounted() {
    this.loadDocuments()
  },

  methods: {
    async loadDocuments() {
      this.loading = true
      try {
        const res = await getPendingDocuments({ page: this.currentPage, page_size: this.pageSize })
        this.documentList = res.data?.items || []
        this.total = res.data?.total || this.documentList.length
      } catch (error) {
        console.error('加载文档列表失败:', error)
        ElMessage.error('加载文档列表失败')
      } finally {
        this.loading = false
      }
    },

    async viewDetail(doc) {
      this.selectedDocument = doc
      this.documentContent = ''
      this.chunks = []
      this.vectorPreview = []
      try {
        const res = await getDocumentDetail(doc.doc_id || doc.id)
        this.documentContent = res.content || res.data?.content || doc.content || ''
        if (res.file_path) {
          this.selectedDocument.file_path = res.file_path
        }
      } catch (error) {
        console.error('获取文档详情失败:', error)
        this.documentContent = '无法加载文档内容'
      }
    },

    async openFile() {
      if (!this.selectedDocument) {
        ElMessage.warning('请先选择文档')
        return
      }

      try {
        const response = await previewDocument(this.selectedDocument.doc_id || this.selectedDocument.id)
        const blob = new Blob([response.data], { type: response.headers?.['content-type'] || 'application/octet-stream' })
        const blobUrl = URL.createObjectURL(blob)
        const docName = this.selectedDocument.doc_name || this.selectedDocument.name || 'document'


        const link = document.createElement('a')
        link.href = blobUrl
        link.setAttribute('download', docName)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        setTimeout(() => URL.revokeObjectURL(blobUrl), 1000)
      } catch (error) {
        console.error('下载或预览文件失败:', error)
        ElMessage.error('无法获取文件')
      }
    },

    async previewChunks() {
      if (!this.selectedDocument) {
        ElMessage.warning('请先选择文档')
        return
      }
      this.processingChunks = true
      try {
        const res = await previewChunks(this.selectedDocument.doc_id || this.selectedDocument.id, {
          chunk_size: this.processParams.chunk_size,
          chunk_overlap: this.processParams.chunk_overlap
        })
        const resultData = res.data || res
        this.chunks = resultData.chunks || []
        if (this.chunks.length > 0) {
          ElMessage.success(`切分完成，共 ${this.chunks.length} 个文本块`)
        }
        this.vectorPreview = []
      } catch (error) {
        console.error('预览切分失败:', error)
        ElMessage.error('预览切分失败')
      } finally {
        this.processingChunks = false
      }
    },

    async generateVectors() {
      if (!this.selectedDocument || !this.chunks.length) {
        ElMessage.warning('请先预览切分')
        return
      }
      this.processingVectors = true
      try {
        const response = await generateVectors(this.selectedDocument.doc_id || this.selectedDocument.id, {
          chunks: this.chunks.map(c => ({ content: c.content || c }))
        })

        if (response.data?.vectors) {
          this.vectorPreview = response.data.vectors
          ElMessage.success(`向量生成完成，共 ${response.data.vectors.length} 个向量`)
        } else if (response.data?.embeddings) {
          this.vectorPreview = response.data.embeddings
          ElMessage.success(`向量生成完成，共 ${response.data.embeddings.length} 个向量`)
        }
      } catch (error) {
        console.error('生成向量失败:', error)
        ElMessage.error('生成向量失败')
      } finally {
        this.processingVectors = false
      }
    },

    async approveAndParseDocument() {
      if (!this.selectedDocument) return

      try {
        await ElMessageBox.confirm(
            `确定要通过文档 "${this.selectedDocument.doc_name}" 并入库吗？`,
            '审核确认',
            {
              confirmButtonText: '确定入库',
              cancelButtonText: '取消',
              type: 'success'
            }
        )

        this.processing = true

        if (!this.chunks.length) {
          await this.previewChunks()
        }

        const approveData = {
          chunks: this.chunks.map(c => ({ content: c.content || c }))
        }

        await approveDocument(this.selectedDocument.doc_id, approveData)
        ElMessage.success('文档审核通过并已入库')
        this.loadDocuments()
        this.selectedDocument = null
        this.chunks = []
        this.vectorPreview = []
      } catch (error) {
        if (error !== 'cancel') {
          console.error('审核入库失败:', error)
          ElMessage.error('审核入库失败')
        }
      } finally {
        this.processing = false
      }
    },

    rejectDocument(document) {
      this.rejectForm.documentId = document.doc_id || document.id
      this.rejectForm.reason = ''
      this.rejectDialogVisible = true
    },

    async confirmReject() {
      if (!this.rejectForm.reason.trim()) {
        ElMessage.warning('请输入驳回原因')
        return
      }
      try {
        await rejectDocument(this.rejectForm.documentId, { reason: this.rejectForm.reason })
        ElMessage.success('文档已驳回')
        this.rejectDialogVisible = false
        this.loadDocuments()
        if (this.selectedDocument && (this.selectedDocument.doc_id === this.rejectForm.documentId || this.selectedDocument.id === this.rejectForm.documentId)) {
          this.selectedDocument = null
          this.chunks = []
          this.vectorPreview = []
        }
      } catch (error) {
        console.error('驳回文档失败:', error)
        ElMessage.error('驳回文档失败')
      }
    },

    formatTime(value) {
      if (!value) return '刚刚'
      if (typeof value === 'string' && (value.includes('T') || value.endsWith('Z'))) {
        try {
          return value.replace(/T/, ' ').replace(/Z$/, '')
        } catch (e) {
          return value
        }
      }

      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return String(value)
      return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
    },
  }
}
</script>

<style scoped>
.doc-workbench {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.el-card {
  border-radius: 28px;
  border: 1px solid rgba(70, 85, 116, 0.08);
  margin-bottom: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 253, 0.97));
  box-shadow: 0 12px 26px rgba(18, 28, 45, 0.05);
}

.el-card :deep(.el-card__header) {
  border-bottom: 1px solid rgba(125, 138, 164, 0.12);
}

.el-card :deep(.el-card__body) {
  padding: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-weight: 700;
  color: var(--rv-text);
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.list-card {
  box-shadow: 0 12px 26px rgba(18, 28, 45, 0.05);
}

.pagination-container {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.detail-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 253, 0.97));
}

.three-column-layout {
  display: grid;
  grid-template-columns: 1fr 1.4fr 1.4fr;
  gap: 20px;
  margin-bottom: 28px;
}

.column {
  background: linear-gradient(180deg, rgba(247, 249, 252, 0.92), rgba(255, 255, 255, 0.96));
  border-radius: 22px;
  padding: 20px 18px;
  border: 1px solid rgba(72, 88, 117, 0.08);
  min-width: 0;
}

.column h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #2c3e50;
}

.badge {
  background: rgba(49, 94, 251, 0.08);
  color: var(--rv-primary);
  font-size: 12px;
  font-weight: 700;
  padding: 6px 10px;
  border-radius: 999px;
}

.config-column :deep(.el-form-item) {
  margin-bottom: 18px;
}

.config-column :deep(.el-form-item__label) {
  font-weight: 500;
  color: #34495e;
}

.preview-content {
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(72, 88, 117, 0.08);
  min-height: 300px;
  max-height: 360px;
  overflow: hidden;
}

.chunk-item, .vector-item {
  padding: 12px 14px;
  border-bottom: 1px solid #f0f2f5;
}

.chunk-item:last-child, .vector-item:last-child {
  border-bottom: none;
}

.chunk-header, .vector-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 12px;
}

.chunk-index, .vector-index {
  background-color: rgba(49, 94, 251, 0.08);
  padding: 2px 8px;
  border-radius: 30px;
  color: var(--rv-primary);
  font-weight: 700;
}

.chunk-len, .vector-dim {
  color: #8c8c8c;
}

.chunk-text {
  font-size: 13px;
  line-height: 1.6;
  color: #1f2d3d;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  background-color: #f8f9fa;
  padding: 6px 8px;
  border-radius: 10px;
  font-family: 'SF Mono', monospace;
}

.vector-values {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  background-color: #f8f9fa;
  padding: 6px 8px;
  border-radius: 10px;
  color: #44506a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.more-hint {
  padding: 8px;
  text-align: center;
  color: #999;
  font-size: 12px;
  background: #fafafa;
}

.action-bar {
  margin-top: 16px;
  padding-top: 18px;
  border-top: 1px dashed rgba(72, 88, 117, 0.14);
  display: flex;
  justify-content: flex-end;
}

.action-bar .el-button-group {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.empty-detail {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 253, 0.97));
  border-radius: 28px;
  padding: 40px 0;
  box-shadow: 0 12px 26px rgba(18, 28, 45, 0.05);
}

@media (max-width: 1200px) {
  .three-column-layout {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
</style>
