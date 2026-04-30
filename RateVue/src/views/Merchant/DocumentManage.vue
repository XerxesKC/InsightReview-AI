<template>
  <div class="merchant-document-container">

    <el-card class="box-card upload-section" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="header-title">上传新文档</span>
        </div>
      </template>

      <div class="upload-layout-centered">
        <el-upload
            v-show="!currentFile"
            class="upload-dropzone"
            drag
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleFileChange"
            :limit="1"
            ref="uploadRef"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="upload-tip text-center">
              支持 pdf, docx, txt, md, csv 格式。<br/>
              仅上传至临时目录/OSS，等待提交审核。
            </div>
          </template>
        </el-upload>

        <div v-if="currentFile" class="selected-file-card">
          <div class="file-basic-info">
            <el-icon class="file-icon"><Document /></el-icon>
            <div class="file-details">
              <div
                  class="file-name clickable"
                  :title="'点击预览: ' + currentFile.name"
                  @click="previewLocalFile(currentFile)"
              >
                {{ currentFile.name }}
              </div>
              <div class="file-size">{{ formatFileSize(currentFile.size) }}</div>
            </div>
            <el-button
                v-if="!isUploading"
                type="danger"
                text
                bg
                icon="Delete"
                @click="handleFileRemove"
                class="remove-btn"
            >
              删除
            </el-button>
          </div>

          <div class="progress-area" v-if="isUploading || uploadProgress > 0">
            <span class="progress-text">{{ uploadProgress === 100 ? '上传完成' : '正在上传...' }}</span>
            <el-progress
                :percentage="uploadProgress"
                :status="uploadProgress === 100 ? 'success' : ''"
                :stroke-width="8"
            />
          </div>
        </div>

        <div class="action-group">
          <el-button
              type="primary"
              size="large"
              class="submit-btn"
              @click="submitUpload"
              :loading="isUploading"
              :disabled="!currentFile"
          >
            <el-icon v-if="!isUploading"><Upload /></el-icon>
            {{ isUploading ? '上传中...' : '提交审核' }}
          </el-button>
        </div>
      </div>
    </el-card>


    <el-card class="box-card list-section" shadow="never">
      <template #header>
        <div class="card-header list-header">
          <span class="header-title">文档列表</span>
          <div class="filter-group">
            <el-radio-group v-model="filterStatus" size="small">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="pending">待审核</el-radio-button>
              <el-radio-button label="approved">已通过</el-radio-button>
              <el-radio-button label="rejected">已驳回</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <el-table :data="paginatedList" style="width: 100%" v-loading="loading">
        <el-table-column prop="docName" label="文档名称" min-width="250" show-overflow-tooltip />
        <el-table-column prop="docSize" label="大小" width="120">
          <template #default="scope">
            {{ formatFileSize(scope.row.docSize) }}
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="上传时间" width="180" />
        <el-table-column prop="status" label="审核状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" effect="light">
              {{ getStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button link type="primary" size="small" @click="handlePreview(scope.row)">预览</el-button>
            <el-button link type="warning" size="small" @click="handleEdit(scope.row)" :disabled="scope.row.status === 'processing'">
              {{ scope.row.status === 'rejected' ? '查看驳回/重提' : '编辑' }}
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(scope.row)" :disabled="scope.row.status === 'processing'">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-container" v-if="filteredList.length > 0">
        <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="filteredList.length"
            background
            layout="total, prev, pager, next, jumper"
        />
      </div>
    </el-card>

    <el-dialog v-model="editDialogVisible" title="编辑文档" width="500px">
      <el-alert
          v-if="editForm.status === 'rejected'"
          title="文档被驳回"
          :description="editForm.rejectReason"
          type="error"
          show-icon
          :closable="false"
          style="margin-bottom: 20px;"
      />

      <el-form :model="editForm" label-width="80px">
        <el-form-item label="文档名称">
          <el-input v-model="editForm.docName" disabled />
        </el-form-item>
        <el-form-item label="重新上传">
          <el-upload
              action="#"
              :auto-upload="false"
              :limit="1"
              :on-change="handleEditFileChange"
              :show-file-list="false"
          >
            <el-button size="small">选择新文件</el-button>
            <span v-if="editForm.newFile" style="margin-left: 10px; font-size: 12px; color: #409eff;">
              已选: {{ editForm.newFile.name }}
            </span>
            <template #tip>
              <div class="el-upload__tip">（不保留原文件，上传后新文件将覆盖原文件）</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showHistory">回滚</el-button>
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEdit">保存并提交审核</el-button>
        </span>
      </template>
    </el-dialog>
    <el-dialog v-model="historyDialogVisible" title="文档历史版本" width="700px">
      <div v-loading="historyLoading">
        <el-table :data="historyList" border stripe v-if="historyList.length">
          <el-table-column prop="doc_id" label="文档ID" width="80" align="center" />
          <el-table-column prop="doc_name" label="文档名称" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'pending' ? 'warning' : 'info'">
                {{ row.status === 'approved' ? '已审核' : row.status === 'pending' ? '待审核' :
                  row.status === 'deprecated' ? '已弃用' : row.status === 'rejected' ? '已驳回' : row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="doc_size" label="文件大小" width="100" align="center">
            <template #default="{ row }">
              {{ formatFileSize(row.doc_size) }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" align="center">
            <template #default="{ row }">
              {{ new Date(row.created_at).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                type="primary"
                @click="handleRollback(row)"
                :disabled="row.status === 'pending'"
              >
                回滚
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="没有历史版本" :image-size="80" />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="historyDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">

import { ref, computed, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Document, Upload } from '@element-plus/icons-vue'
import {
  uploadDocument,
  getDocumentList,
  deleteDocument,
  updateDocument,
  downloadDocument,
  checkDuplicateDocument,
  deprecatedDocument,
  getDocumentHistory,
  activateDocument
} from '@/api/document'
import { useMerchantInfoStore } from "@/stores/merchantInfo";

const loading = ref(false)
const filterStatus = ref('')
const uploadRef = ref(null)

const currentFile = ref(null)
const isUploading = ref(false)
const uploadProgress = ref(0)

const merchantStore = useMerchantInfoStore()
const documentList = ref([])
const editDialogVisible = ref(false)
const editForm = reactive({ id: null, docName: '', status: '', rejectReason: '', newFile: null })
const currentPage = ref(1)
const pageSize = ref(10)

const historyDialogVisible = ref(false)
const historyList = ref([])
const historyLoading = ref(false)

const documentParams = reactive({
  uploaderId: merchantStore.merchantInfo.merchantId,
  uploaderType: 'merchant',
})
const fetchDocuments = async () => {
  loading.value = true
  try {
    const query = {
      user_id: documentParams.uploaderId,
      user_type: documentParams.uploaderType
    }

    const response = await getDocumentList(query)
    const resData = response.data || response
    const items = resData.items || []

    documentList.value = items
        .filter(item => item.status !== 'deprecated')// 过滤掉状态为deprecated的文件
        .map(item => ({
          id: item.doc_id,
          docName: item.doc_name,
          docSize: item.doc_size,
          status: item.status,
          createdAt: item.created_at ? new Date(item.created_at).toLocaleString() : '',
      }))
  } catch (error) {
    console.error('获取列表失败:', error)
    ElMessage.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDocuments()
})
const filteredList = computed(() => {
  if (!filterStatus.value) return documentList.value
  return documentList.value.filter(item => item.status === filterStatus.value)
})
const paginatedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredList.value.slice(start, end)
})
watch(filterStatus, () => {
  currentPage.value = 1
})

const getStatusType = (status) => {
  const map = { pending: 'warning', approved: 'success', rejected: 'danger' }
  return map[status] || 'info'
}
const getStatusLabel = (status) => {
  const map = { pending: '待审核', approved: '已通过', rejected: '已驳回' }
  return map[status] || '未知'
}
const formatFileSize = (bytes) => {
  if (bytes === 0 || !bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const handleFileChange = (uploadFile) => {
  currentFile.value = uploadFile.raw
  uploadProgress.value = 0
}

const handleFileRemove = () => {
  currentFile.value = null
  uploadProgress.value = 0
  if (uploadRef.value) uploadRef.value.clearFiles()
}

const previewLocalFile = (file) => {
  if (!file) return
  if (file.type === 'application/pdf' || file.type === 'text/plain' || file.name.toLowerCase().endsWith('.pdf')) {
    const objectUrl = URL.createObjectURL(file)
    window.open(objectUrl, '_blank')
  } else {
    ElMessage.info('该文件格式不支持在浏览器直接预览，请提交后由系统处理。')
  }
}

const handlePreview = async (row) => {
  try {
    const response = await downloadDocument(row.id)

    let blobData;
    let contentType;

    if (response instanceof Blob) {
      blobData = response;
      contentType = response.type;
    } else {
      blobData = response.data || response;
      contentType = response.headers?.['content-type'] || blobData.type;
    }

    const isPdfOrTxt = row.docName.toLowerCase().endsWith('.pdf') || row.docName.toLowerCase().endsWith('.txt')
    const isTxt = row.docName.toLowerCase().endsWith('.txt')

    if (isTxt) {
      if (!contentType || !contentType.toLowerCase().includes('charset')) {
        contentType = 'text/plain; charset=utf-8';
      }
    }

    const blob = new Blob([blobData], { type: contentType })
    const blobUrl = URL.createObjectURL(blob)
    if (isPdfOrTxt) {
      window.open(blobUrl, '_blank')
    } else {
      const link = document.createElement('a')
      link.href = blobUrl
      link.setAttribute('download', row.docName)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }

    setTimeout(() => {
      URL.revokeObjectURL(blobUrl)
    }, 1000)

  } catch (error) {
    console.error('下载或预览文件失败:', error)
    ElMessage.error('无法获取文件，可能已被删除或服务器出错')
  }
}

const uploadParams = reactive({
  uploaderId: merchantStore.merchantInfo.merchantId,
  uploaderType:'merchant',
})

const submitUpload = async () => {
  if (!currentFile.value) return;

  isUploading.value = true
  uploadProgress.value = 0

  const formData = new FormData()
  formData.append('uploader_id', uploadParams.uploaderId)
  formData.append('uploader_type', uploadParams.uploaderType)
  formData.append('file', currentFile.value)

  try {
    const duplicateCheckResponse = await checkDuplicateDocument({
      doc_name: currentFile.value.name,
      uploader_type: uploadParams.uploaderType,
      uploader_id: uploadParams.uploaderId
    })
    if (duplicateCheckResponse.data?.exists) {
      await ElMessageBox.confirm(
        `有同名文件"${currentFile.value.name}"，即将覆盖，是否继续？`,
        '文件覆盖提示',
        {
          confirmButtonText: '确定覆盖',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )

      if (duplicateCheckResponse.data.duplicate_documents?.length > 0) {
        for (const doc of duplicateCheckResponse.data.duplicate_documents) {
          await deprecatedDocument(doc.doc_id)
        }
      }
    }

    const response = await uploadDocument(formData, (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      uploadProgress.value = percentCompleted
    })

    const data = response.data || response

    const newDoc = {
      id: data.doc_id,
      docName: currentFile.value.name,
      docSize: currentFile.value.size,
      status: data.status,
      createdAt: new Date().toLocaleString(),
      rejectReason: '',
      url: data.file_path
    }

    documentList.value.unshift(newDoc)

    setTimeout(() => {
      handleFileRemove()
      isUploading.value = false
      ElMessage.success('文档上传成功！')
      fetchDocuments()
    }, 500)

  } catch (error) {
    console.error('上传失败:', error)
    isUploading.value = false
    uploadProgress.value = 0
    const errorMsg = error.response?.data?.detail || error.message || '文件上传失败'
    ElMessage.error(errorMsg)
  }
}

const handleEdit = (row) => {
  editForm.id = row.id
  editForm.docName = row.docName
  editForm.status = row.status
  editForm.rejectReason = row.rejectReason
  editForm.newFile = null
  editDialogVisible.value = true
}

const handleEditFileChange = (uploadFile) => {
  editForm.newFile = uploadFile.raw
}

const submitEdit = async () => {
  if (!editForm.newFile) {
    ElMessage.warning('请选择要重新上传的新文件')
    return
  }

  loading.value = true

  const formData = new FormData()
  formData.append('doc_id', editForm.id)
  formData.append('file', editForm.newFile)

  try {
    await updateDocument(formData)

    ElMessage.success('已成功重新提交审核！')
    editDialogVisible.value = false

    await fetchDocuments()

  } catch (error) {
    console.error('重新提交失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '提交失败，请重试'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}

const showHistory = async () => {
  historyLoading.value = true
  try {
    const response = await getDocumentHistory({
      doc_name: editForm.docName,
      uploader_type: 'merchant',
      uploader_id: merchantStore.merchantInfo.merchantId,
      current_doc_id: editForm.id
    })

    const data = response.data || response
    historyList.value = data.items || []
    historyDialogVisible.value = true
  } catch (error) {
    console.error('获取历史版本失败:', error)
    ElMessage.error('获取历史版本失败')
  } finally {
    historyLoading.value = false
  }
}

const handleRollback = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要回滚到版本 "${row.doc_name}" 吗？回滚后将激活该版本并弃用当前版本。`,
      '确认回滚',
      {
        confirmButtonText: '确定回滚',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await activateDocument(row.doc_id)

    if (editForm.id) {
      await deprecatedDocument(editForm.id)
    }
    ElMessage.success('回滚成功')
    historyDialogVisible.value = false
    editDialogVisible.value = false

    await fetchDocuments()

  } catch (error) {
    if (error !== 'cancel') {
      console.error('回滚失败:', error)
      ElMessage.error('回滚失败')
    }
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除文档 "${row.docName}" 吗？删除后不可恢复。`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await deleteDocument(row.id)

      const index = documentList.value.findIndex(item => item.id === row.id)
      if (index !== -1) {
        documentList.value.splice(index, 1)
      }
      ElMessage.success('删除成功')

    } catch (error) {
      console.error('删除失败:', error)
      const errorMsg = error.response?.data?.detail || '删除失败，请稍后重试'
      ElMessage.error(errorMsg)
    }
  }).catch(() => {
  })
}
</script>

<style scoped>
.merchant-document-container { padding: 24px; display: flex; flex-direction: column; gap: 24px; background-color: #f5f7fa; min-height: 100vh; }
.header-title { font-size: 16px; font-weight: 600; color: #303133; }
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.upload-layout-centered {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 650px;
  margin: 10px auto;
}
::v-deep(.el-upload-dragger) { background-color: #fcfcfd; border-radius: 8px; transition: all 0.3s ease; padding: 40px 0; }
::v-deep(.el-upload-dragger:hover) { background-color: #f2f6fc; border-color: #409eff; }
.upload-tip { color: #909399; font-size: 12px; line-height: 1.6; margin-top: 10px; }
.text-center { text-align: center; }

.selected-file-card { background: #f8f9fa; border: 1px solid #e4e7ed; border-radius: 8px; padding: 20px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05); }
.file-basic-info { display: flex; align-items: center; gap: 16px; }
.file-icon { font-size: 36px; color: #909399; }
.file-details { flex: 1; overflow: hidden; }

.file-name.clickable {
  font-size: 14px;
  font-weight: 500;
  color: #409eff;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  text-decoration: underline;
  transition: color 0.3s;
}
.file-name.clickable:hover { color: #66b1ff; }

.file-size { font-size: 12px; color: #909399; }
.remove-btn { font-size: 14px; }
.progress-area { margin-top: 20px; }
.progress-text { font-size: 12px; color: #606266; margin-bottom: 8px; display: inline-block; }

.action-group { text-align: center; }
.submit-btn { width: 220px; border-radius: 6px; }

.merchant-document-container {
  border-radius: 24px;
}

.merchant-document-container :deep(.el-card) {
  border-radius: 22px;
  border: 1px solid rgba(190, 214, 205, 0.78);
  box-shadow: 0 18px 44px rgba(22, 53, 45, 0.08);
  background: rgba(255, 255, 255, 0.82);
  overflow: hidden;
}

.merchant-document-container :deep(.el-table th.el-table__cell) {
  background: #eef8f4;
  color: #226b5b;
}

.merchant-document-container :deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

.merchant-document-container :deep(.el-button--primary) {
  background: #2f7d6b;
  border-color: #2f7d6b;
}

.merchant-document-container :deep(.el-upload-dragger) {
  border-color: rgba(47, 125, 107, 0.26);
  background: rgba(246, 251, 249, 0.92);
}
</style>
