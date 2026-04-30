<template>
  <div class="doc-workbench">
    <h2>智能文档拆分工作台</h2>

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
            <el-button size="small" type="danger" plain @click="openRejectDialog(scope.row)">驳回</el-button>
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

    <div v-if="selectedDocument">
      <el-card class="detail-card" shadow="never">
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
            <el-form :model="splitConfig" label-position="top" size="default">
              <el-form-item label="拆分策略">
                <el-radio-group v-model="splitConfig.strategy">
                  <el-radio value="recursive">
                    <el-tooltip content="基于分隔符递归切分，速度快，适合结构化文本" placement="top">
                      <span>递归切分</span>
                    </el-tooltip>
                  </el-radio>
                  <el-radio value="semantic">
                    <el-tooltip content="基于语义相似度切分，保持话题完整，适合长文档" placement="top">
                      <span>语义切分</span>
                    </el-tooltip>
                  </el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="块大小 (chunk_size)">
                <el-slider v-model.number="splitConfig.chunk_size" :min="100" :max="1000" :step="50" show-input />
              </el-form-item>

              <el-form-item label="重叠量 (overlap)">
                <el-slider
                    v-model.number="splitConfig.chunk_overlap"
                    :min="0"
                    :max="splitConfig.chunk_size - 20"
                    :step="10"
                    show-input
                    :disabled="splitConfig.chunk_size <= 50"
                />
              </el-form-item>

              <template v-if="splitConfig.strategy === 'semantic'">
                <el-form-item label="相似度阈值">
                  <el-slider
                      v-model.number="splitConfig.similarity_threshold"
                      :min="0.1"
                      :max="0.9"
                      :step="0.05"
                      show-input
                      :format-tooltip="val => val.toFixed(2)"
                  />
                </el-form-item>

                <el-form-item label="语义模型">
                  <el-select
                      v-model="splitConfig.model_name"
                      placeholder="选择模型"
                      :loading="loadingModels"
                      style="width: 100%"
                  >
                    <el-option
                        v-for="model in availableModels"
                        :key="model.path"
                        :label="model.name"
                        :value="model.path"
                    />
                  </el-select>
                </el-form-item>
              </template>
            </el-form>
          </div>

          <div class="column preview-column">
            <h4>拆分预览 <span v-if="chunks.length" class="badge">{{ chunks.length }}块</span></h4>
            <div class="preview-content" v-loading="splitting">
              <el-scrollbar max-height="400px" v-if="chunks.length">
                <div v-for="(chunk, idx) in chunks" :key="idx" class="chunk-item">
                  <div class="chunk-header">
                    <span class="chunk-index">#{{ idx + 1 }}</span>
                    <span class="chunk-len">{{ chunk.length || (chunk.content?.length || 0) }} 字符</span>
                  </div>
                  <div class="chunk-text">{{ chunk.content || chunk }}</div>
                  <div class="chunk-meta" v-if="chunk.similarity">
                    与前一块相似度: {{ (chunk.similarity * 100).toFixed(1) }}%
                  </div>
                </div>
              </el-scrollbar>
              <el-empty v-else description="点击「拆分预览」生成块" :image-size="80" />
            </div>
          </div>

          <div class="column vector-column">
            <h4>向量预览 <span v-if="vectors.length" class="badge">{{ vectors.length }}项</span></h4>
            <div class="preview-content" v-loading="vectorLoading">
              <el-scrollbar max-height="400px" v-if="vectors.length">
                <div v-for="(vec, idx) in vectors.slice(0, 20)" :key="idx" class="vector-item">
                  <div class="vector-header">
                    <span class="vector-index">块 {{ idx + 1 }}</span>
                    <span class="vector-dim">维度 {{ vec.length }}</span>
                  </div>
                  <div class="vector-values">
                    [ {{ vec.slice(0, 6).map(v => v.toFixed(3)).join(', ') }}{{ vec.length > 6 ? '...' : '' }} ]
                  </div>
                </div>
                <div v-if="vectors.length > 20" class="more-hint">仅展示前20项</div>
              </el-scrollbar>
              <el-empty v-else description="点击「生成向量」预览" :image-size="80" />
            </div>
          </div>
        </div>

        <div class="action-bar">
          <el-button-group>
            <el-button @click="openFile" :disabled="!selectedDocument" size="large">
              <el-icon><FolderOpened /></el-icon> 打开文件
            </el-button>
            <el-button @click="previewSplit" :loading="splitting" size="large" :disabled="!selectedDocument">
              <el-icon><View /></el-icon> 拆分预览
            </el-button>
            <el-button @click="previewVectors" :loading="vectorLoading" size="large" :disabled="!chunks.length">
              <el-icon><DataLine /></el-icon> 生成向量
            </el-button>
            <el-button type="success" @click="approveAndStore" :loading="storing" size="large">
              <el-icon><Check /></el-icon> 审核入库
            </el-button>
          </el-button-group>
        </div>
      </el-card>
    </div>

    <el-empty v-else description="请从左侧列表选择一份文档开始处理" :image-size="120" class="empty-detail" />

    <el-dialog v-model="rejectDialogVisible" title="驳回文档" width="400px">
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="驳回原因">
          <el-input v-model="rejectForm.reason" type="textarea" :rows="3" placeholder="请输入驳回原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmReject" :loading="rejectLoading">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Document, FolderOpened, View, DataLine, Check } from '@element-plus/icons-vue'
import {
  getPendingDocuments,
  getDocumentDetail,
  rejectDocument,
  approveDocument,
  previewDocument
} from '@/api/documentWorkbench'
import { previewIntelligentChunks, generateVectors } from '@/api/newDocumentWorkbench'
import { getEmbeddingModels } from '@/api/system'
import {downloadDocument} from "@/api/document";

export default {
  name: 'NewDocumentWorkbench',
  components: { Refresh, Document, FolderOpened, View, DataLine, Check },

  setup() {
    const documentList = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(20)
    const loading = ref(false)

    const selectedDocument = ref(null)

    const loadingModels = ref(false)
    const modelList = ref([])

    const availableModels = computed(() =>
        modelList.value.filter(item => !item.name.includes('/1_Pooling'))
    )

    const splitConfig = reactive({
      strategy: 'recursive',
      chunk_size: 500,
      chunk_overlap: 50,
      similarity_threshold: 0.7,
      model_name: ''
    })

    const chunks = ref([])
    const splitting = ref(false)

    const vectors = ref([])
    const vectorLoading = ref(false)

    const storing = ref(false)

    const rejectDialogVisible = ref(false)
    const rejectForm = reactive({
      documentId: null,
      reason: ''
    })
    const rejectLoading = ref(false)

    const fetchEmbeddingModels = async () => {
      loadingModels.value = true
      try {
        const res = await getEmbeddingModels()
        const data = res || { models: [] }
        modelList.value = Array.isArray(data.models) ? data.models : []

        if (data.activeModelName) {
          const hit = modelList.value.find(m => m.name === data.activeModelName)
          if (hit) {
            splitConfig.model_name = hit.path
          }
        } else if (data.activeModelPath) {
          const hit = modelList.value.find(m => m.path === data.activeModelPath)
          if (hit) {
            splitConfig.model_name = hit.path
          }
        } else if (availableModels.value.length > 0) {
          splitConfig.model_name = availableModels.value[0]?.path || ''
        }
      } catch (error) {
        console.error('获取模型列表失败:', error)
        ElMessage.error(`获取模型列表失败：${error?.message || '未知错误'}`)
        splitConfig.model_name = 'data/bge-model/BAAI/bge-base-zh-v1.5'
      } finally {
        loadingModels.value = false
      }
    }

    const loadDocuments = async () => {
      loading.value = true
      try {
        const res = await getPendingDocuments({
          page: currentPage.value,
          page_size: pageSize.value
        })
        documentList.value = res.data?.items || []
        total.value = res.data?.total || documentList.value.length
      } catch (error) {
        console.error('加载文档列表失败:', error)
        ElMessage.error('加载文档列表失败')
      } finally {
        loading.value = false
      }
    }

    const viewDetail = async (doc) => {
      selectedDocument.value = doc
      chunks.value = []
      vectors.value = []
      try {
        const res = await getDocumentDetail(doc.doc_id || doc.id)
        const filePath = res?.file_path || res?.data?.file_path || res?.data?.document?.file_path
        if (filePath) {
          selectedDocument.value.file_path = filePath
        }
      } catch (error) {
        console.error('获取文档详情失败:', error)
      }
    }

    const openFile = async () => {
      if (!selectedDocument.value) {
        ElMessage.warning('请先选择文档')
        return
      }

      const docId = selectedDocument.value.doc_id || selectedDocument.value.id
      const docName = selectedDocument.value.doc_name || selectedDocument.value.docName || 'document'

      try {
        const response = await previewDocument(docId)

        let blobData;
        let contentType;

        if (response instanceof Blob) {
          blobData = response;
          contentType = response.type;
        } else if (response.data) {
          blobData = response.data;
          contentType = response.headers?.['content-type'] || 'application/octet-stream';
        } else {
          blobData = response;
          contentType = 'application/octet-stream';
        }

        const fileExt = docName.toLowerCase().split('.').pop()
        const isPdfOrTxt = fileExt === 'pdf' || fileExt === 'txt'
        const isTxt = fileExt === 'txt'

        let finalContentType = contentType
        if (isTxt && (!contentType || !contentType.toLowerCase().includes('charset'))) {
          finalContentType = 'text/plain; charset=utf-8';
        }

        const blob = new Blob([blobData], { type: finalContentType })
        const blobUrl = URL.createObjectURL(blob)

        if (isPdfOrTxt) {
          window.open(blobUrl, '_blank')
        } else {
          const link = document.createElement('a')
          link.href = blobUrl
          link.setAttribute('download', docName)
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        }

        setTimeout(() => {
          URL.revokeObjectURL(blobUrl)
        }, 1000)

      } catch (error) {
        console.error('下载或预览文件失败:', error)
        ElMessage.error(`无法获取文件: ${error.message || '未知错误'}`)
      }
    }

    const previewSplit = async () => {
      if (!selectedDocument.value) {
        ElMessage.warning('请先选择文档')
        return
      }

      splitting.value = true
      try {
        const params = {
          chunk_size: splitConfig.chunk_size,
          chunk_overlap: splitConfig.chunk_overlap,
          splitter_type: splitConfig.strategy
        }

        if (splitConfig.strategy === 'semantic') {
          params.similarity_threshold = splitConfig.similarity_threshold
          params.model_name = splitConfig.model_name
        }

        const res = await previewIntelligentChunks(
            selectedDocument.value.doc_id || selectedDocument.value.id,
            params
        )

        const resultData = res.data || res
        chunks.value = resultData.chunks || []

        if (chunks.value.length > 0) {
          ElMessage.success(`切分完成，共 ${chunks.value.length} 个文本块`)
        }

        vectors.value = []
      } catch (error) {
        console.error('预览切分失败:', error)
        ElMessage.error('预览切分失败')
      } finally {
        splitting.value = false
      }
    }

    const previewVectors = async () => {
      if (!selectedDocument.value || !chunks.value.length) {
        ElMessage.warning('请先预览拆分')
        return
      }

      vectorLoading.value = true
      try {
        const response = await generateVectors(
            selectedDocument.value.doc_id || selectedDocument.value.id,
            {
              chunks: chunks.value.map(c => ({ content: c.content || c }))
            }
        )

        if (response.data?.vectors) {
          vectors.value = response.data.vectors
          ElMessage.success(`向量生成完成，共 ${response.data.vectors.length} 个向量`)
        } else if (response.data?.embeddings) {
          vectors.value = response.data.embeddings
          ElMessage.success(`向量生成完成，共 ${response.data.embeddings.length} 个向量`)
        }
      } catch (error) {
        console.error('生成向量失败:', error)
        ElMessage.error('生成向量失败')
      } finally {
        vectorLoading.value = false
      }
    }

    const approveAndStore = async () => {
      if (!selectedDocument.value) return

      try {
        await ElMessageBox.confirm(
            `确定要通过文档 "${selectedDocument.value.doc_name}" 并入库吗？`,
            '审核确认',
            {
              confirmButtonText: '确定入库',
              cancelButtonText: '取消',
              type: 'success'
            }
        )

        storing.value = true

        if (!chunks.value.length) {
          await previewSplit()
        }

        const approveData = {
          chunks: chunks.value.map(c => ({ content: c.content || c })),
          target_index: 'default_vector_index',
          splitter_info: {
            strategy: splitConfig.strategy,
            chunk_size: splitConfig.chunk_size,
            chunk_overlap: splitConfig.chunk_overlap,
            ...(splitConfig.strategy === 'semantic' && {
              similarity_threshold: splitConfig.similarity_threshold,
              model_name: splitConfig.model_name
            })
          }
        }

        await approveDocument(selectedDocument.value.doc_id, approveData)
        ElMessage.success('文档审核通过并已入库')

        await loadDocuments()
        selectedDocument.value = null
        chunks.value = []
        vectors.value = []
      } catch (error) {
        if (error !== 'cancel') {
          console.error('审核入库失败:', error)
          ElMessage.error('审核入库失败')
        }
      } finally {
        storing.value = false
      }
    }

    const openRejectDialog = (doc) => {
      rejectForm.documentId = doc.doc_id || doc.id
      rejectForm.reason = ''
      rejectDialogVisible.value = true
    }

    const confirmReject = async () => {
      if (!rejectForm.reason.trim()) {
        ElMessage.warning('请输入驳回原因')
        return
      }

      rejectLoading.value = true
      try {
        await rejectDocument(rejectForm.documentId, { reason: rejectForm.reason })
        ElMessage.success('文档已驳回')
        rejectDialogVisible.value = false
        await loadDocuments()

        if (selectedDocument.value &&
            (selectedDocument.value.doc_id === rejectForm.documentId ||
                selectedDocument.value.id === rejectForm.documentId)) {
          selectedDocument.value = null
          chunks.value = []
          vectors.value = []
        }
      } catch (error) {
        console.error('驳回文档失败:', error)
        ElMessage.error('驳回文档失败')
      } finally {
        rejectLoading.value = false
      }
    }

    const formatTime = (value) => {
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
    }

    onMounted(() => {
      Promise.all([
        loadDocuments(),
        fetchEmbeddingModels()
      ])
    })

    return {
      documentList,
      total,
      currentPage,
      pageSize,
      loading,
      selectedDocument,
      splitConfig,
      chunks,
      splitting,
      vectors,
      loadingModels,
      availableModels,
      vectorLoading,
      storing,
      rejectDialogVisible,
      rejectForm,
      rejectLoading,
      loadDocuments,
      viewDetail,
      openFile,
      previewSplit,
      previewVectors,
      approveAndStore,
      openRejectDialog,
      confirmReject,
      formatTime,
    }
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

.column {
  background: linear-gradient(180deg, rgba(247, 249, 252, 0.92), rgba(255, 255, 255, 0.96));
  border-radius: 22px;
  padding: 20px 18px;
  border: 1px solid rgba(72, 88, 117, 0.08);
  min-width: 0;
}

.three-column-layout {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1.2fr;
  gap: 20px;
  margin-bottom: 28px;
}

.analysis-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 253, 0.97));
  margin-top: 24px;
}

.analysis-content {
  padding: 10px 0;
}

.analysis-input {
  margin-bottom: 12px;
}

.analysis-result-container {
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px solid rgba(72, 88, 117, 0.08);
  height: 500px;
  padding: 10px;
  overflow: hidden;
}

.result-chart {
  background: #f8f9fa;
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 12px;
  text-align: center;
}

.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bar-row {
  display: grid;
  grid-template-columns: 120px 1fr 80px;
  align-items: center;
  gap: 10px;
}

.bar-label {
  text-align: right;
  color: #606266;
  font-size: 12px;
}

.bar-track {
  height: 10px;
  background: #ebeef5;
  border-radius: 999px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #5b8ff9 0%, #61d9a5 100%);
  border-radius: 999px;
}

.bar-value {
  text-align: left;
  color: #303133;
  font-size: 12px;
  font-weight: 600;
}

.result-text {
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 13px;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: #f4f4f5;
  padding: 10px;
  border-radius: 6px;
}

.result-summary {
  margin-top: 10px;
}

.sandbox-preview {
  margin-top: 10px;
  background: #f0f9ff;
  border: 1px solid #d9ecff;
}

.code-collapse :deep(.el-collapse-item__header) {
  font-size: 12px;
  color: #909399;
  height: 36px;
  line-height: 36px;
}

.code-block {
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 12px;
  color: #c7254e;
  background-color: #f9f2f4;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0;
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
  height: 400px;
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
  border-radius: 6px;
  font-family: 'SF Mono', monospace;
}

.chunk-meta {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
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
  margin-top: 12px;
  padding-top: 16px;
  border-top: 1px dashed #dcdfe6;
  display: flex;
  justify-content: flex-end;
}

.action-bar .el-button-group {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.empty-detail {
  background: white;
  border-radius: 16px;
  padding: 40px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

@media (max-width: 1400px) {
  .three-column-layout {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 900px) {
  .three-column-layout {
    grid-template-columns: 1fr;
  }
}
</style>
