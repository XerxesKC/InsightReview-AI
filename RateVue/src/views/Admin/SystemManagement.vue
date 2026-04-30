<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import {
  getEmbeddingModels,
  setActiveEmbeddingModel,
  getSystemParams,
  updateSystemParams
} from '@/api/system'

interface EmbeddingModelItem {
  name: string
  path: string
  dimension?: number | null
  description?: string
}

interface EmbeddingModelsResponse {
  activeModelName?: string
  activeModelPath?: string
  models: EmbeddingModelItem[]
}

interface SystemParams {
  chunkSize: number
  chunkOverlap: number
  fileUploadMaxSizeMB: number
  vectorStorePath: string
  requestTimeoutMs: number
  chatMaxContextTurns: number
  chatMaxContextTokens: number
  chatRetrievalTopK: number
  chatSimilarityThreshold: number
  chatAnswerMaxChars: number
  chatRetrievalTimeoutMs: number
  chatGenerationTimeoutMs: number
  chatVectorCacheEnabled: boolean
  chatVectorCacheBackend: 'auto' | 'redis' | 'memory' | 'none'
  chatVectorCacheTtlSeconds: number
  chatContextBackend: 'auto' | 'redis' | 'mysql'
}

const vectorCacheBackendOptions = ['auto', 'redis', 'memory', 'none'] as const
const contextBackendOptions = ['auto', 'redis', 'mysql'] as const

const toSafeNumber = (value: unknown, fallback: number) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

const toSafeBoolean = (value: unknown, fallback: boolean) => {
  if (typeof value === 'boolean') return value
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (normalized === 'true') return true
    if (normalized === 'false') return false
  }
  if (typeof value === 'number') {
    if (value === 1) return true
    if (value === 0) return false
  }
  return fallback
}

const toSafeBackend = (
    value: unknown,
    fallback: SystemParams['chatVectorCacheBackend']
): SystemParams['chatVectorCacheBackend'] => {
  const normalized = String(value ?? '').trim().toLowerCase()
  return vectorCacheBackendOptions.includes(normalized as any)
      ? (normalized as SystemParams['chatVectorCacheBackend'])
      : fallback
}

const toSafeContextBackend = (
    value: unknown,
    fallback: SystemParams['chatContextBackend']
): SystemParams['chatContextBackend'] => {
  const normalized = String(value ?? '').trim().toLowerCase()
  return contextBackendOptions.includes(normalized as any)
      ? (normalized as SystemParams['chatContextBackend'])
      : fallback
}

const loadingModels = ref(false)
const savingModel = ref(false)
const modelList = ref<EmbeddingModelItem[]>([])
const selectedModelPath = ref('')

const visibleModelList = computed(() =>
    modelList.value.filter(item => !item.name.includes('/1_Pooling'))
)

const fetchEmbeddingModels = async () => {
  loadingModels.value = true
  try {
    const res: any = await getEmbeddingModels()
    const data = res || { models: [] }

    modelList.value = Array.isArray(data.models) ? data.models : []

    if (data.activeModelName) {
      const hit = modelList.value.find(m => m.name === data.activeModelName)
      selectedModelPath.value = hit?.path || ''
    } else if (data.activeModelPath) {
      const hit = modelList.value.find(m => m.path === data.activeModelPath)
      selectedModelPath.value = hit?.path || ''
    } else {
      selectedModelPath.value = ''
    }
  } catch (error: any) {
    ElMessage.error(`获取模型列表失败：${error?.message || '未知错误'}`)
  } finally {
    loadingModels.value = false
  }
}

const saveActiveModel = async () => {
  if (!selectedModelPath.value) {
    ElMessage.warning('请先选择一个 Embedding 模型')
    return
  }

  const selected = visibleModelList.value.find(m => m.path === selectedModelPath.value)
  if (!selected) {
    ElMessage.warning('当前选择的模型无效，请重新选择')
    return
  }

  savingModel.value = true
  try {
    const res: any = await setActiveEmbeddingModel({
      modelName: selected.name,
      modelPath: selected.path
    })

    if (res && res.success === false) {
      ElMessage.error(res.message || 'Embedding 模型保存失败')
      return
    }

    ElMessage.success('Embedding 模型已更新')
    await fetchEmbeddingModels()
  } catch (error: any) {
    ElMessage.error(`保存模型失败：${error?.message || '未知错误'}`)
  } finally {
    savingModel.value = false
  }
}

const loadingParams = ref(false)
const savingParams = ref(false)
const paramsFormRef = ref<FormInstance>()
const paramsForm = reactive<SystemParams>({
  chunkSize: 500,
  chunkOverlap: 50,
  fileUploadMaxSizeMB: 20,
  vectorStorePath: '/data/chroma',
  requestTimeoutMs: 30000,
  chatMaxContextTurns: 10,
  chatMaxContextTokens: 3000,
  chatRetrievalTopK: 6,
  chatSimilarityThreshold: 0.35,
  chatAnswerMaxChars: 500,
  chatRetrievalTimeoutMs: 6000,
  chatGenerationTimeoutMs: 20000,
  chatVectorCacheEnabled: true,
  chatVectorCacheBackend: 'auto',
  chatVectorCacheTtlSeconds: 300,
  chatContextBackend: 'auto'
})

const lastConfirmedChatContextBackend = ref<SystemParams['chatContextBackend']>('auto')

const paramsRules: FormRules = {
  chunkSize: [{ required: true, message: '请输入默认文本拆分大小', trigger: 'blur' }],
  chunkOverlap: [{ required: true, message: '请输入文本重叠大小', trigger: 'blur' }],
  fileUploadMaxSizeMB: [{ required: true, message: '请输入文件上传大小限制', trigger: 'blur' }],
  vectorStorePath: [{ required: true, message: '请输入向量库存储路径', trigger: 'blur' }],
  requestTimeoutMs: [{ required: true, message: '请输入接口超时时间', trigger: 'blur' }],
  chatMaxContextTurns: [{ required: true, message: '请输入上下文最大轮数', trigger: 'blur' }],
  chatMaxContextTokens: [{ required: true, message: '请输入上下文最大Token数', trigger: 'blur' }],
  chatRetrievalTopK: [{ required: true, message: '请输入检索TopK', trigger: 'blur' }],
  chatSimilarityThreshold: [{ required: true, message: '请输入相似度阈值', trigger: 'blur' }],
  chatAnswerMaxChars: [{ required: true, message: '请输入回答最大长度', trigger: 'blur' }],
  chatRetrievalTimeoutMs: [{ required: true, message: '请输入检索超时时间', trigger: 'blur' }],
  chatGenerationTimeoutMs: [{ required: true, message: '请输入生成超时时间', trigger: 'blur' }],
  chatVectorCacheBackend: [{ required: true, message: '请选择向量缓存后端', trigger: 'change' }],
  chatVectorCacheTtlSeconds: [{ required: true, message: '请输入向量缓存TTL(秒)', trigger: 'blur' }],
  chatContextBackend: [{ required: true, message: '请选择上下文缓存后端', trigger: 'change' }]
}

const buildSystemParamsPayload = () => ({
  chunkSize: paramsForm.chunkSize,
  chunkOverlap: paramsForm.chunkOverlap,
  fileUploadMaxSizeMB: paramsForm.fileUploadMaxSizeMB,
  vectorStorePath: paramsForm.vectorStorePath,
  requestTimeoutMs: paramsForm.requestTimeoutMs,
  chatMaxContextTurns: paramsForm.chatMaxContextTurns,
  chatMaxContextTokens: paramsForm.chatMaxContextTokens,
  chatRetrievalTopK: paramsForm.chatRetrievalTopK,
  chatSimilarityThreshold: paramsForm.chatSimilarityThreshold,
  chatAnswerMaxChars: paramsForm.chatAnswerMaxChars,
  chatRetrievalTimeoutMs: paramsForm.chatRetrievalTimeoutMs,
  chatGenerationTimeoutMs: paramsForm.chatGenerationTimeoutMs,
  chatVectorCacheEnabled: paramsForm.chatVectorCacheEnabled,
  chatVectorCacheBackend: paramsForm.chatVectorCacheBackend,
  chatVectorCacheTtlSeconds: paramsForm.chatVectorCacheTtlSeconds,
  chatContextBackend: paramsForm.chatContextBackend
})

const fetchSystemParams = async () => {
  loadingParams.value = true
  try {
    const res: any = await getSystemParams()
    const d = res || {}

    paramsForm.chunkSize = toSafeNumber(d.chunkSize, paramsForm.chunkSize)
    paramsForm.chunkOverlap = toSafeNumber(d.chunkOverlap, paramsForm.chunkOverlap)
    paramsForm.fileUploadMaxSizeMB = toSafeNumber(d.fileUploadMaxSizeMB, paramsForm.fileUploadMaxSizeMB)
    paramsForm.vectorStorePath = String(d.vectorStorePath ?? paramsForm.vectorStorePath)
    paramsForm.requestTimeoutMs = toSafeNumber(d.requestTimeoutMs, paramsForm.requestTimeoutMs)
    paramsForm.chatMaxContextTurns = toSafeNumber(d.chatMaxContextTurns, paramsForm.chatMaxContextTurns)
    paramsForm.chatMaxContextTokens = toSafeNumber(d.chatMaxContextTokens, paramsForm.chatMaxContextTokens)
    paramsForm.chatRetrievalTopK = toSafeNumber(d.chatRetrievalTopK, paramsForm.chatRetrievalTopK)
    paramsForm.chatSimilarityThreshold = toSafeNumber(d.chatSimilarityThreshold, paramsForm.chatSimilarityThreshold)
    paramsForm.chatAnswerMaxChars = toSafeNumber(d.chatAnswerMaxChars, paramsForm.chatAnswerMaxChars)
    paramsForm.chatRetrievalTimeoutMs = toSafeNumber(d.chatRetrievalTimeoutMs, paramsForm.chatRetrievalTimeoutMs)
    paramsForm.chatGenerationTimeoutMs = toSafeNumber(d.chatGenerationTimeoutMs, paramsForm.chatGenerationTimeoutMs)
    paramsForm.chatVectorCacheEnabled = toSafeBoolean(d.chatVectorCacheEnabled, paramsForm.chatVectorCacheEnabled)
    paramsForm.chatVectorCacheBackend = toSafeBackend(d.chatVectorCacheBackend, paramsForm.chatVectorCacheBackend)
    paramsForm.chatVectorCacheTtlSeconds = toSafeNumber(d.chatVectorCacheTtlSeconds, paramsForm.chatVectorCacheTtlSeconds)
    paramsForm.chatContextBackend = toSafeContextBackend(d.chatContextBackend, paramsForm.chatContextBackend)
    lastConfirmedChatContextBackend.value = paramsForm.chatContextBackend
  } catch (error: any) {
    ElMessage.error(`获取系统参数失败：${error?.message || '未知错误'}`)
  } finally {
    loadingParams.value = false
  }
}

const handleContextBackendChange = async (value: SystemParams['chatContextBackend']) => {
  if (value !== 'redis') {
    return
  }

  try {
    const res: any = await updateSystemParams(buildSystemParamsPayload())
    if (res && res.success === false) {
      ElMessage.error(res.message || '上下文缓存后端切换失败')
      paramsForm.chatContextBackend = lastConfirmedChatContextBackend.value
      return
    }
    lastConfirmedChatContextBackend.value = value
  } catch (error: any) {
    ElMessage.error(error?.message || '上下文缓存后端切换失败')
    paramsForm.chatContextBackend = lastConfirmedChatContextBackend.value
  }
}

const submitSystemParams = async () => {
  if (!paramsFormRef.value) return

  await paramsFormRef.value.validate(async (valid) => {
    if (!valid) return

    if (paramsForm.chunkOverlap >= paramsForm.chunkSize) {
      ElMessage.warning('文本重叠大小必须小于文本拆分大小')
      return
    }

    if (paramsForm.chatSimilarityThreshold < 0 || paramsForm.chatSimilarityThreshold > 1) {
      ElMessage.warning('相似度阈值必须在 0 到 1 之间')
      return
    }

    if (!vectorCacheBackendOptions.includes(paramsForm.chatVectorCacheBackend)) {
      ElMessage.warning('向量缓存后端配置无效')
      return
    }

    if (!Number.isInteger(paramsForm.chatVectorCacheTtlSeconds) || paramsForm.chatVectorCacheTtlSeconds < 0) {
      ElMessage.warning('向量缓存TTL必须是大于等于 0 的整数')
      return
    }

    savingParams.value = true
    try {
      const res: any = await updateSystemParams({
        ...buildSystemParamsPayload()
      })

      if (res && res.success === false) {
        ElMessage.error(res.message || '系统参数保存失败')
        return
      }

      lastConfirmedChatContextBackend.value = paramsForm.chatContextBackend
      ElMessage.success('系统参数保存成功')
    } catch (error: any) {
      ElMessage.error(`保存系统参数失败：${error?.message || '未知错误'}`)
    } finally {
      savingParams.value = false
    }
  })
}

onMounted(async () => {
  await Promise.all([fetchEmbeddingModels(), fetchSystemParams()])
})
</script>

<template>
  <div class="system-management">
    <el-card class="section-card" shadow="never" v-loading="loadingModels">
      <template #header>
        <div class="card-header">
          <span>模型配置</span>
        </div>
      </template>

      <div class="hint">
        仅展示后端服务器本地已存在的 Embedding 模型，请选择一个作为当前生效模型。
      </div>

      <el-table :data="visibleModelList" border stripe>
        <el-table-column label="选择" width="80" align="center">
          <template #default="{ row }">
            <el-radio :model-value="selectedModelPath" :label="row.path" @change="selectedModelPath = row.path">
              &nbsp;
            </el-radio>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="模型名称" min-width="180" />
        <el-table-column prop="path" label="模型路径" min-width="320" show-overflow-tooltip />
        <el-table-column prop="dimension" label="维度" width="120">
          <template #default="{ row }">
            {{ row.dimension ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
      </el-table>

      <div class="actions">
        <el-button :loading="loadingModels" @click="fetchEmbeddingModels">刷新模型列表</el-button>
        <el-button type="primary" :loading="savingModel" @click="saveActiveModel">保存当前选择</el-button>
      </div>
    </el-card>

    <el-card class="section-card" shadow="never" v-loading="loadingParams">
      <template #header>
        <div class="card-header">
          <span>系统参数</span>
        </div>
      </template>

      <el-form
          ref="paramsFormRef"
          :model="paramsForm"
          :rules="paramsRules"
          label-width="190px"
          class="params-form"
      >
        <el-form-item label="默认文本拆分大小" prop="chunkSize">
          <el-input-number v-model="paramsForm.chunkSize" :min="1" :step="50" />
        </el-form-item>

        <el-form-item label="默认文本重叠大小" prop="chunkOverlap">
          <el-input-number v-model="paramsForm.chunkOverlap" :min="0" :step="10" />
        </el-form-item>

        <el-form-item label="文件上传大小限制(MB)" prop="fileUploadMaxSizeMB">
          <el-input-number v-model="paramsForm.fileUploadMaxSizeMB" :min="1" :step="1" />
        </el-form-item>

        <el-form-item label="向量库存储路径" prop="vectorStorePath">
          <el-input v-model="paramsForm.vectorStorePath" />
        </el-form-item>

        <el-form-item label="接口请求超时时间(ms)" prop="requestTimeoutMs">
          <el-input-number v-model="paramsForm.requestTimeoutMs" :min="1000" :step="1000" />
        </el-form-item>

        <el-form-item label="上下文最大轮数" prop="chatMaxContextTurns">
          <el-input-number v-model="paramsForm.chatMaxContextTurns" :min="1" :step="1" />
        </el-form-item>

        <el-form-item label="上下文最大Token数" prop="chatMaxContextTokens">
          <el-input-number v-model="paramsForm.chatMaxContextTokens" :min="100" :step="100" />
        </el-form-item>

        <el-form-item label="检索Top K" prop="chatRetrievalTopK">
          <el-input-number v-model="paramsForm.chatRetrievalTopK" :min="1" :step="1" />
        </el-form-item>

        <el-form-item label="相似度阈值" prop="chatSimilarityThreshold">
          <el-input-number v-model="paramsForm.chatSimilarityThreshold" :min="0" :max="1" :step="0.01" :precision="2" />
        </el-form-item>

        <el-form-item label="单轮回答最大字数" prop="chatAnswerMaxChars">
          <el-input-number v-model="paramsForm.chatAnswerMaxChars" :min="100" :step="50" />
        </el-form-item>

        <el-form-item label="检索超时时间(ms)" prop="chatRetrievalTimeoutMs">
          <el-input-number v-model="paramsForm.chatRetrievalTimeoutMs" :min="100" :step="100" />
        </el-form-item>

        <el-form-item label="生成超时时间(ms)" prop="chatGenerationTimeoutMs">
          <el-input-number v-model="paramsForm.chatGenerationTimeoutMs" :min="100" :step="100" />
        </el-form-item>

        <el-form-item label="启用向量缓存" prop="chatVectorCacheEnabled">
          <el-switch v-model="paramsForm.chatVectorCacheEnabled" />
        </el-form-item>

        <el-form-item label="向量缓存后端" prop="chatVectorCacheBackend">
          <el-select v-model="paramsForm.chatVectorCacheBackend" placeholder="请选择向量缓存后端" style="width: 260px">
            <el-option label="auto（优先 Redis，不可用回退内存）" value="auto" />
            <el-option label="redis（仅 Redis）" value="redis" />
            <el-option label="memory（仅内存）" value="memory" />
            <el-option label="none（关闭缓存）" value="none" />
          </el-select>
        </el-form-item>

        <el-form-item label="向量缓存TTL(秒)" prop="chatVectorCacheTtlSeconds">
          <el-input-number v-model="paramsForm.chatVectorCacheTtlSeconds" :min="0" :step="30" />
        </el-form-item>

        <el-form-item label="上下文缓存后端" prop="chatContextBackend">
          <el-select
              v-model="paramsForm.chatContextBackend"
              placeholder="请选择上下文缓存后端"
              style="width: 260px"
              @change="handleContextBackendChange"
          >
            <el-option label="auto（优先 Redis，不可用回退 MySQL）" value="auto" />
            <el-option label="redis（仅 Redis）" value="redis" />
            <el-option label="mysql（仅 MySQL）" value="mysql" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="savingParams" @click="submitSystemParams">保存系统参数</el-button>
          <el-button @click="fetchSystemParams">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.system-management {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-card {
  border-radius: 28px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 253, 0.97));
}

.section-card :deep(.el-card__header) {
  border-bottom: 1px solid rgba(125, 138, 164, 0.12);
}

.section-card :deep(.el-card__body) {
  padding: 24px;
}

.card-header {
  font-weight: 700;
  color: var(--rv-text);
  letter-spacing: 0.02em;
}

.hint {
  margin-bottom: 18px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(49, 94, 251, 0.06);
  color: var(--rv-text-soft);
  font-size: 13px;
  line-height: 1.7;
}

.actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.params-form {
  max-width: 920px;
}

.system-management :deep(.el-table) {
  border-radius: 20px;
  overflow: hidden;
}

.system-management :deep(.el-form-item) {
  margin-bottom: 18px;
}

.system-management :deep(.el-input-number),
.system-management :deep(.el-input),
.system-management :deep(.el-select) {
  width: min(100%, 320px);
}

.system-management :deep(.el-radio) {
  margin-right: 0;
}

@media (max-width: 960px) {
  .actions {
    justify-content: stretch;
    flex-direction: column;
  }

  .system-management :deep(.el-input-number),
  .system-management :deep(.el-input),
  .system-management :deep(.el-select) {
    width: 100%;
  }
}
</style>
