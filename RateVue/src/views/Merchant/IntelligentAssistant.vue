<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatLineRound,
  Delete,
  Document,
  EditPen,
  Microphone,
  Picture,
  Plus,
  Promotion,
  Setting,
  User,
  DocumentAdd
} from '@element-plus/icons-vue'
import { useMerchantInfoStore } from '@/stores/merchantInfo'
import {
  clearChatSessionContext,
  deleteChatSession,
  getChatSessionRetrievalConfig,
  getChatSessionHistory,
  getChatSessions,
  rollbackChatSession,
  streamChatCompletion,
  uploadChatImage,
  getChatImageBlob,
  updateChatSessionRetrievalConfig,
  updateChatSessionTitle,
  updateChatTurnRating,
  uploadChatFile
} from '@/api/chat'
import {getSystemParams} from "@/api/system";
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import { downloadDocument } from '@/api/document'

const HISTORY_SYNC_RETRY_DELAYS = [300, 800, 1600]
const QUICK_QUESTION_TEMPLATES = [
  '常见的商家违规行为有哪些？对应什么处罚？', '帮我查一下我点赞量最高的动态是哪条。'
]
const MAX_CHAT_IMAGE_COUNT = 1
const MAX_CHAT_IMAGE_SIZE = 10 * 1024 * 1024

const ALLOWED_CHAT_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp']
const ALLOWED_CHAT_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'bmp']

const ALLOWED_DATA_FILE_EXTENSIONS = ['csv', 'xlsx', 'xls', 'txt', 'md', 'pdf', 'docx']
const MAX_DATA_FILE_SIZE = 50 * 1024 * 1024

const merchantInfoStore = useMerchantInfoStore()

const inputMessage = ref('')
const sessions = ref([])
const currentSessionId = ref('')
const historyItems = ref([])
const chatMessages = ref([])
const sessionsLoading = ref(false)
const historyLoading = ref(false)
const sending = ref(false)
const clearing = ref(false)
const renaming = ref(false)
const retrievalConfigLoading = ref(false)
const retrievalConfigSaving = ref(false)
const deletingSessionId = ref('')
const rollbackingTurnNo = ref(null)
const messageViewport = ref(null)
const historyRequestToken = ref(0)
const streamAbortController = ref(null)
const activeStreamState = ref(null)
const sessionRetrievalConfig = ref({
  top_k: null,
  similarity_threshold: null
})
const globalRetrievalDefaults = ref({
  top_k: 6,
  similarity_threshold: 0.35
})
const speechRecognitionSupported = ref(false)
const speechRecognition = ref(null)
const isListening = ref(false)
const speechShouldKeepListening = ref(false)
const speechRestartTimer = ref(null)
const speechDraftPrefix = ref('')
const speechFinalTranscript = ref('')
const imageUploadInputRef = ref(null)
const selectedChatImages = ref([])
const fileUploadInputRef = ref(null)
const selectedChatFiles = ref([])
const fileUploading = ref(false)
const imageUploading = ref(false)
const imagePreviewVisible = ref(false)
const previewImageUrl = ref('')
const previewImageName = ref('')
const previewImageLoading = ref(false)

const extractFileName = (url = '', fallbackId = '') => {
  if (url) {
    const parts = url.split('/')
    const name = parts[parts.length - 1]
    if (name && name.includes('.')) return name
  }
  return fallbackId ? `图片-${String(fallbackId).slice(-6)}.png` : '附带图片'
}

const saveTurnImageMeta = (sessionId, turnNo, meta) => {
  if (!sessionId || !turnNo || (!meta.imageId && !meta.fileName)) return;
  try {
    localStorage.setItem(`chat_img_${sessionId}_${turnNo}`, JSON.stringify(meta));
  } catch (e) {}
}

const getTurnImageMeta = (sessionId, turnNo) => {
  if (!sessionId || !turnNo) return null;
  try {
    const val = localStorage.getItem(`chat_img_${sessionId}_${turnNo}`);
    return val ? JSON.parse(val) : null;
  } catch(e) { return null; }
}

const handlePreviewMessageImage = async (message) => {
  if (!message.imageId) return

  previewImageName.value = message.fileName || extractFileName(message.imageUrl, message.imageId)
  previewImageLoading.value = true
  imagePreviewVisible.value = true
  
  try {
    const response = await getChatImageBlob(message.imageId, getRequestHeaders())
    let blobData = response.data || response
    let contentType = response.headers?.['content-type'] || blobData?.type || 'image/jpeg'
    const blob = new Blob([blobData], { type: contentType })
    previewImageUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '获取图片失败'))
    imagePreviewVisible.value = false
  } finally {
    previewImageLoading.value = false
  }
}

watch(imagePreviewVisible, (newVal) => {
  if (!newVal && previewImageUrl.value) {
    setTimeout(() => {
      URL.revokeObjectURL(previewImageUrl.value)
      previewImageUrl.value = ''
    }, 300)
  }
})

const currentSessionMeta = computed(() => sessions.value.find(item => item.session_id === currentSessionId.value) || null)
const activeHistoryItems = computed(() => historyItems.value.filter(item => item.is_active !== false))
const hasActiveConversation = computed(() => activeHistoryItems.value.length > 0)
const sessionTurnList = computed(() => [...historyItems.value].sort((a, b) => (b.turn_no || 0) - (a.turn_no || 0)))
const currentUserName = computed(() => merchantInfoStore.merchantInfo.merchantName || merchantInfoStore.merchantInfo.nickname || '我')

const getRequestHeaders = () => ({
  'X-User-Id': String(merchantInfoStore.merchantInfo.merchantId || ''),
  'X-User-Type': String(merchantInfoStore.merchantInfo.merchantType || 'merchant')
})

const getPayload = (response) => {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response || {}
}

const getErrorMessage = (error, fallback = '操作失败，请稍后重试') => {
  if (typeof error === 'string') return error
  if (error?.message) return error.message
  if (error?.msg) return error.msg
  if (error?.data?.message) return error.data.message
  return fallback
}

const getFileExtension = (fileName = '') => {
  const index = fileName.lastIndexOf('.')
  return index >= 0 ? fileName.slice(index + 1).toLowerCase() : ''
}

const isAllowedChatImage = (file) => {
  if (!file) return false

  const mimeType = String(file.type || '').toLowerCase()
  const extension = getFileExtension(file.name)

  return ALLOWED_CHAT_IMAGE_TYPES.includes(mimeType)
      || ALLOWED_CHAT_IMAGE_EXTENSIONS.includes(extension)
}

const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms))

const toNullableNumber = (value) => {
  if (value === null || value === undefined || value === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

const resolveGlobalRetrievalConfig = async () => {
  const response = await getSystemParams()
  const payload = getPayload(response)
  const topK = toNullableNumber(payload.chatRetrievalTopK)
  const similarityThreshold = toNullableNumber(payload.chatSimilarityThreshold)

  if (topK === null || topK < 1 || similarityThreshold === null || similarityThreshold < 0 || similarityThreshold > 1) {
    throw new Error('全局检索参数无效')
  }

  const normalized = {
    top_k: Math.floor(topK),
    similarity_threshold: similarityThreshold
  }

  globalRetrievalDefaults.value = normalized
  return normalized
}

const applyGlobalRetrievalConfigToSession = async (sessionId) => {
  if (!sessionId) return null

  let globalConfig = { ...globalRetrievalDefaults.value }
  try {
    globalConfig = await resolveGlobalRetrievalConfig()
  } catch (error) {
  }

  await updateChatSessionRetrievalConfig(sessionId, {
    top_k: globalConfig.top_k,
    similarity_threshold: globalConfig.similarity_threshold
  }, getRequestHeaders())

  sessionRetrievalConfig.value = { ...globalConfig }
  return globalConfig
}

const formatTime = (value) => {
  if (!value) return '刚刚'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatSourceDisplayName = (source = {}) => {
  const docName = typeof source.source === 'string' && source.source.trim()
    ? source.source.trim()
    : '未命名文档'
  const kbName = typeof source.kb_name === 'string' ? source.kb_name.trim() : ''

  return kbName ? `${docName}（${kbName}）` : docName
}

const normalizeSessionItems = (items = []) => items
    .filter(item => item && item.is_deleted !== true)
    .map(item => ({
      session_id: item.session_id,
      title: item.title || '未命名会话',
      turn_count: Number(item.turn_count || 0),
      active_turn_count: Number(item.active_turn_count || 0),
      created_at: item.created_at || null,
      updated_at: item.updated_at || null,
      is_deleted: item.is_deleted === true
    }))
    .sort((a, b) => new Date(b.updated_at || b.created_at || 0).getTime() - new Date(a.updated_at || a.created_at || 0).getTime())

const normalizeHistoryItems = (items = [], sessionId = currentSessionId.value) => items
    .map(item => {
      const turnNo = Number(item.turn_no || 0)
      let imgId = item.image_id || null
      let imgUrl = item.image_url || ''
      let fName = item.file_name || ''

      if (sessionId && turnNo > 0) {
        const cached = getTurnImageMeta(sessionId, turnNo)
        if (cached) {
          if (!imgId && cached.imageId) imgId = cached.imageId
          if (!imgUrl && cached.imageUrl) imgUrl = cached.imageUrl
          if (!fName && cached.fileName) fName = cached.fileName
        }
      }

      return {
        turn_id: item.turn_id || item.id || item.turn_no || Date.now(),
        turn_no: turnNo,
        query: item.query || '',
        answer: item.answer || '',
        rewritten_query: item.rewritten_query || null,
        sources: Array.isArray(item.sources) ? item.sources : [],
        created_at: item.created_at || null,
        is_active: item.is_active !== false,
        rating: Number(item.rating || 0),
        input_type: item.input_type || null,
        ocr_text: item.ocr_text || '',
        image_id: imgId,
        image_url: imgUrl,
        fileName: fName || extractFileName(imgUrl, imgId)
      }
    })
    .sort((a, b) => (a.turn_no || 0) - (b.turn_no || 0))

const scrollChatToBottom = async () => {
  await nextTick()
  if (messageViewport.value) {
    messageViewport.value.scrollTop = messageViewport.value.scrollHeight
  }
}

const patchChatMessage = (messageId, patch) => {
  chatMessages.value = chatMessages.value.map((message) => {
    if (message.id !== messageId) return message

    return {
      ...message,
      ...(typeof patch === 'function' ? patch(message) : patch)
    }
  })
}

const syncChatMessages = () => {
  const nextMessages = []

  activeHistoryItems.value
      .slice()
      .sort((a, b) => (a.turn_no || 0) - (b.turn_no || 0))
      .forEach(item => {
        nextMessages.push({
          id: `user-${item.turn_id}-${item.turn_no}`,
          role: 'user',
          content: item.query,
          turnNo: item.turn_no,
          createdAt: item.created_at,
          inputType: item.input_type || null,
          ocrText: item.ocr_text || '',
          ocrExpanded: false,
          imageId: item.image_id || null,
          imageUrl: item.image_url || '',
          fileName: item.fileName || ''
        })

        nextMessages.push({
          id: `assistant-${item.turn_id}-${item.turn_no}`,
          role: 'assistant',
          content: item.answer,
          turnNo: item.turn_no,
          createdAt: item.created_at,
          sources: item.sources,
          rewrittenQuery: item.rewritten_query,
          isStreaming: false,
          rating: item.rating || 0,
          turnId: item.turn_id
        })
      })

  chatMessages.value = nextMessages
  scrollChatToBottom()
}

const applyHistoryItems = (items) => {
  historyItems.value = normalizeHistoryItems(items)
  syncChatMessages()
}

const appendImmediateTurn = (turn) => {
  const mergedTurns = currentSessionId.value
      ? [...historyItems.value.filter(item => item.turn_no !== turn.turn_no), turn]
      : [turn]

  historyItems.value = normalizeHistoryItems(mergedTurns)
  syncChatMessages()
}

const handleRating = async (message, rating) => {
  const newRating = message.rating === rating ? 0 : rating

  try {
    await updateChatTurnRating({
      session_id: currentSessionId.value,
      turn_no: message.turnNo,
      rating: newRating
    }, getRequestHeaders())

    patchChatMessage(message.id, {
      rating: newRating
    })

    const historyItem = historyItems.value.find(item => item.turn_no === message.turnNo)
    if (historyItem) {
      historyItem.rating = newRating
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '更新评分失败'))
  }
}

const resetDraftConversation = () => {
  historyRequestToken.value += 1
  currentSessionId.value = ''
  historyItems.value = []
  chatMessages.value = []
  sessionRetrievalConfig.value = { ...globalRetrievalDefaults.value }
  inputMessage.value = ''
  selectedChatImages.value = []
}

const triggerImagePicker = () => {
  if (sending.value || imageUploading.value) return
  imageUploadInputRef.value?.click()
}

const removeSelectedImage = () => {
  selectedChatImages.value = []
  if (imageUploadInputRef.value) {
    imageUploadInputRef.value.value = ''
  }
}

const handleSelectChatImage = async (event) => {
  const file = event?.target?.files?.[0]
  if (!file) return

  if (selectedChatImages.value.length >= MAX_CHAT_IMAGE_COUNT) {
    ElMessage.warning(`最多上传 ${MAX_CHAT_IMAGE_COUNT} 张图片`)
    event.target.value = ''
    return
  }
  if (!isAllowedChatImage(file)) {
    ElMessage.warning(`仅支持 ${ALLOWED_CHAT_IMAGE_EXTENSIONS.join(', ')} 格式图片`)
    event.target.value = ''
    return
  }

  if (file.size > MAX_CHAT_IMAGE_SIZE) {
    ElMessage.warning('图片大小不能超过 10MB')
    event.target.value = ''
    return
  }

  imageUploading.value = true
  try {
    const response = await uploadChatImage(file, getRequestHeaders())
    const payload = getPayload(response)
    const imageId = payload.image_id
    const imageUrl = payload.image_url

    if (!imageId || !imageUrl) {
      ElMessage.error('图片上传成功但返回字段不完整')
      return
    }

    selectedChatImages.value = [{
      imageId,
      imageUrl,
      fileName: file.name,
      size: file.size
    }]
    ElMessage.success('图片上传成功')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '图片上传失败'))
  } finally {
    imageUploading.value = false
    event.target.value = ''
  }
}

const triggerFilePicker = () => {
  if (sending.value || fileUploading.value) return
  fileUploadInputRef.value?.click()
}

const removeSelectedFile = (index) => {
  selectedChatFiles.value.splice(index, 1)
  if (fileUploadInputRef.value) {
    fileUploadInputRef.value.value = ''
  }
}

const handleSelectDataFile = async (event) => {
  const file = event?.target?.files?.[0]
  if (!file) return
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (!ALLOWED_DATA_FILE_EXTENSIONS.includes(ext)) {
    ElMessage.warning(`仅支持 ${ALLOWED_DATA_FILE_EXTENSIONS.join(', ')} 格式文件`)
    event.target.value = ''
    return
  }
  if (file.size > MAX_DATA_FILE_SIZE) {
    ElMessage.warning('文件大小不能超过 50MB')
    event.target.value = ''
    return
  }
  fileUploading.value = true
  try {
    const response = await uploadChatFile(file, getRequestHeaders())
    const payload = getPayload(response)
    const docId = payload.doc_id
    if (!docId) {
      ElMessage.error('文件上传成功但返回字段不完整')
      return
    }
    selectedChatFiles.value.push({
      docId,
      fileName: file.name,
      size: file.size
    })
    ElMessage.success('文件上传成功')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '文件上传失败'))
  } finally {
    fileUploading.value = false
    event.target.value = ''
  }
}

const loadSessionRetrievalConfig = async (sessionId, { silent = false, fallbackToGlobal = true } = {}) => {
  if (!sessionId) {
    sessionRetrievalConfig.value = { ...globalRetrievalDefaults.value }
    return
  }

  if (!silent) {
    retrievalConfigLoading.value = true
  }

  try {
    const response = await getChatSessionRetrievalConfig(sessionId, getRequestHeaders())
    const payload = getPayload(response)
    const topK = toNullableNumber(payload.top_k)
    const similarityThreshold = toNullableNumber(payload.similarity_threshold)

    if (topK === null || similarityThreshold === null) {
      if (fallbackToGlobal) {
        await applyGlobalRetrievalConfigToSession(sessionId)
      } else {
        sessionRetrievalConfig.value = {
          top_k: toNullableNumber(sessionRetrievalConfig.value.top_k) ?? globalRetrievalDefaults.value.top_k,
          similarity_threshold: toNullableNumber(sessionRetrievalConfig.value.similarity_threshold) ?? globalRetrievalDefaults.value.similarity_threshold
        }
      }
      return
    }

    sessionRetrievalConfig.value = {
      top_k: Math.floor(topK),
      similarity_threshold: similarityThreshold
    }
  } catch (error) {
    sessionRetrievalConfig.value = { ...globalRetrievalDefaults.value }
    ElMessage.error(getErrorMessage(error, '加载会话检索参数失败'))
  } finally {
    if (!silent) {
      retrievalConfigLoading.value = false
    }
  }
}

const saveSessionRetrievalConfig = async () => {
  if (!currentSessionId.value || retrievalConfigSaving.value) return

  const topK = toNullableNumber(sessionRetrievalConfig.value.top_k)
  const similarityThreshold = toNullableNumber(sessionRetrievalConfig.value.similarity_threshold)

  if (topK === null || topK < 1) {
    ElMessage.warning('Top K 请输入大于等于 1 的整数')
    return
  }

  if (similarityThreshold === null || similarityThreshold < 0 || similarityThreshold > 1) {
    ElMessage.warning('相似度阈值需在 0 到 1 之间')
    return
  }

  retrievalConfigSaving.value = true
  try {
    const nextConfig = {
      top_k: Math.floor(topK),
      similarity_threshold: similarityThreshold
    }

    await updateChatSessionRetrievalConfig(currentSessionId.value, {
      top_k: nextConfig.top_k,
      similarity_threshold: nextConfig.similarity_threshold
    }, getRequestHeaders())

    sessionRetrievalConfig.value = { ...nextConfig }
    await loadSessionRetrievalConfig(currentSessionId.value, { silent: true, fallbackToGlobal: false })
    ElMessage.success('会话检索参数已更新')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '更新会话检索参数失败'))
  } finally {
    retrievalConfigSaving.value = false
  }
}

const resetSessionRetrievalConfig = async () => {
  if (!currentSessionId.value || retrievalConfigSaving.value) return

  retrievalConfigSaving.value = true
  try {
    await applyGlobalRetrievalConfigToSession(currentSessionId.value)
    ElMessage.success('已回退到全局检索参数')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '回退全局参数失败'))
  } finally {
    retrievalConfigSaving.value = false
  }
}

const showTimeoutStageMessage = (timeoutStage) => {
  if (timeoutStage === 'retrieval') {
    ElMessage.warning('检索超时，请稍后重试')
  } else if (timeoutStage === 'generation') {
    ElMessage.warning('答案生成超时，请稍后重试')
  }
}

const updateSpeechInput = (interimTranscript = '') => {
  inputMessage.value = `${speechDraftPrefix.value}${speechFinalTranscript.value}${interimTranscript}`
}

const clearSpeechRestartTimer = () => {
  if (speechRestartTimer.value) {
    clearTimeout(speechRestartTimer.value)
    speechRestartTimer.value = null
  }
}

const initSpeechRecognition = () => {
  if (typeof window === 'undefined') return

  const SpeechRecognitionConstructor = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognitionConstructor) return

  const recognition = new SpeechRecognitionConstructor()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true

  recognition.onstart = () => {
    isListening.value = true
    speechDraftPrefix.value = inputMessage.value
    speechFinalTranscript.value = ''
  }

  recognition.onresult = (event) => {
    let interimTranscript = ''

    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const transcript = event.results[index][0]?.transcript || ''
      if (event.results[index].isFinal) {
        speechFinalTranscript.value += transcript
      } else {
        interimTranscript += transcript
      }
    }

    updateSpeechInput(interimTranscript)
  }

  recognition.onerror = (event) => {
    const speechError = event?.error

    if (speechError === 'not-allowed' || speechError === 'service-not-allowed') {
      speechShouldKeepListening.value = false
      ElMessage.warning('请开启麦克风权限后重试')
      return
    }

    if (speechError === 'audio-capture') {
      speechShouldKeepListening.value = false
      ElMessage.warning('未检测到可用麦克风设备')
      return
    }

    if (speechError !== 'no-speech' && speechError !== 'aborted' && speechError !== 'network') {
      ElMessage.warning('语音识别中断，请重试')
    }
  }

  recognition.onend = () => {
    isListening.value = false

    if (!speechShouldKeepListening.value || sending.value) {
      return
    }

    clearSpeechRestartTimer()
    speechRestartTimer.value = setTimeout(() => {
      if (!speechRecognition.value || !speechShouldKeepListening.value || sending.value) return

      try {
        speechRecognition.value.start()
      } catch (error) {
        if (error?.name !== 'InvalidStateError') {
          speechShouldKeepListening.value = false
          ElMessage.warning('语音识别恢复失败，请重试')
        }
      }
    }, 300)
  }

  speechRecognition.value = recognition
  speechRecognitionSupported.value = true
}

const startSpeechInput = () => {
  if (!speechRecognition.value) {
    ElMessage.warning('当前浏览器不支持语音输入')
    return
  }

  if (sending.value) return

  clearSpeechRestartTimer()
  speechShouldKeepListening.value = true

  try {
    speechRecognition.value.start()
  } catch (error) {
    if (error?.name !== 'InvalidStateError') {
      speechShouldKeepListening.value = false
      ElMessage.warning('启动语音输入失败，请重试')
    }
  }
}

const stopSpeechInput = () => {
  speechShouldKeepListening.value = false
  clearSpeechRestartTimer()

  if (speechRecognition.value && isListening.value) {
    speechRecognition.value.stop()
  }
}

const toggleSpeechInput = () => {
  if (speechShouldKeepListening.value || isListening.value) {
    stopSpeechInput()
    return
  }

  startSpeechInput()
}

const loadSessions = async ({ autoActivateFirst = false, targetSessionId = currentSessionId.value } = {}) => {
  sessionsLoading.value = true

  try {
    const response = await getChatSessions({}, getRequestHeaders())
    const payload = getPayload(response)
    const items = Array.isArray(payload.items)
        ? payload.items
        : Array.isArray(payload.records)
            ? payload.records
            : []

    const normalizedItems = normalizeSessionItems(items)
    sessions.value = normalizedItems

    const nextTargetSessionId = targetSessionId && normalizedItems.some(item => item.session_id === targetSessionId)
        ? targetSessionId
        : ''

    if (nextTargetSessionId) {
      currentSessionId.value = nextTargetSessionId
    } else if (!normalizedItems.length) {
      resetDraftConversation()
    } else if (autoActivateFirst) {
      await activateSession(normalizedItems[0])
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '加载会话列表失败'))
  } finally {
    sessionsLoading.value = false
  }
}

const loadSessionHistory = async (sessionId, { silent = false } = {}) => {
  if (!sessionId) {
    historyItems.value = []
    chatMessages.value = []
    return
  }

  currentSessionId.value = sessionId
  const token = ++historyRequestToken.value

  if (!silent) {
    historyLoading.value = true
  }

  try {
    const response = await getChatSessionHistory(sessionId, { include_inactive: true }, getRequestHeaders())
    if (token !== historyRequestToken.value) return

    const payload = getPayload(response)
    const items = Array.isArray(payload.items)
        ? payload.items
        : Array.isArray(payload.records)
            ? payload.records
            : []

    applyHistoryItems(items)
  } catch (error) {
    if (token === historyRequestToken.value) {
      historyItems.value = []
      chatMessages.value = []
      ElMessage.error(getErrorMessage(error, '加载会话历史失败'))
    }
  } finally {
    if (!silent && token === historyRequestToken.value) {
      historyLoading.value = false
    }
  }
}

const syncHistoryAfterSend = async (sessionId, expectedTurnNo) => {
  for (const delay of HISTORY_SYNC_RETRY_DELAYS) {
    await wait(delay)

    try {
      const response = await getChatSessionHistory(sessionId, { include_inactive: true }, getRequestHeaders())
      const payload = getPayload(response)
      const items = Array.isArray(payload.items)
          ? payload.items
          : Array.isArray(payload.records)
              ? payload.records
              : []

      const normalizedItems = normalizeHistoryItems(items)
      const hasExpectedTurn = normalizedItems.some(item => Number(item.turn_no || 0) >= Number(expectedTurnNo || 0))

      if (!hasExpectedTurn) {
        continue
      }

      applyHistoryItems(normalizedItems)
      return true
    } catch (error) {
    }
  }

  return false
}

const activateSession = async (session) => {
  const sessionId = typeof session === 'string' ? session : session?.session_id
  if (!sessionId || sending.value) return

  inputMessage.value = ''
  await loadSessionHistory(sessionId)
  await loadSessionRetrievalConfig(sessionId)
}

const startNewConversation = () => {
  if (sending.value) {
    ElMessage.warning('请等待当前回复完成后再开始新会话')
    return
  }

  resetDraftConversation()
}

const sendTemplateQuestion = async (question) => {
  const content = String(question || '').trim()
  if (!content || sending.value) return

  inputMessage.value = content
  await sendMessage()
}

const stopGeneration = () => {
  if (!sending.value || !streamAbortController.value) return

  if (activeStreamState.value) {
    activeStreamState.value.stoppedByMerchant = true

    patchChatMessage(activeStreamState.value.assistantMessageId, {
      content: activeStreamState.value.answer || '已停止生成',
      isPending: false,
      isStreaming: false,
      isStopped: true
    })
  }

  streamAbortController.value.abort()
}

const sendMessage = async () => {
  if (speechShouldKeepListening.value || isListening.value) {
    stopSpeechInput()
  }

  const content = inputMessage.value.trim()
  const selectedImage = selectedChatImages.value[0] || null
  if ((!content && !selectedImage && !selectedChatFiles.value.length) || sending.value || imageUploading.value || fileUploading.value) return

  if (!merchantInfoStore.merchantInfo.merchantId) {
    ElMessage.warning('当前商家信息未加载完成，请重新登录后再试')
    return
  }

  const previousMessages = chatMessages.value.slice()
  const previousHistoryItems = historyItems.value.slice()
  const previousSessionId = currentSessionId.value || ''
  const now = new Date().toISOString()
  const requestSeed = Date.now()
  const pendingMerchantMessageId = `pending-merchant-${requestSeed}`
  const pendingAssistantMessageId = `pending-assistant-${requestSeed}`
  const streamState = {
    assistantMessageId: pendingAssistantMessageId,
    answer: '',
    stoppedByMerchant: false
  }

  sending.value = true
  inputMessage.value = ''
  activeStreamState.value = streamState
  chatMessages.value = [
    ...previousMessages,
    {
      id: pendingMerchantMessageId,
      role: 'merchant',
      content,
      createdAt: now,
      inputType: selectedImage ? 'image' : 'text',
      ocrText: '',
      ocrExpanded: false,
      imageId: selectedImage?.imageId || null,
      imageUrl: selectedImage?.imageUrl || ''
    },
    {
      id: pendingAssistantMessageId,
      role: 'assistant',
      content: '正在思考中，请稍候…',
      createdAt: now,
      isPending: true,
      isStreaming: true
    }
  ]
  scrollChatToBottom()

  const controller = new AbortController()
  streamAbortController.value = controller

  try {
    const requestData = {
      messages: [{ role: 'merchant', content }],
      stream: true,
      session_id: previousSessionId || null
    }

    if (selectedImage) {
      requestData.image_id = selectedImage.imageId
      requestData.image_url = selectedImage.imageUrl
    }

    if (selectedChatFiles.value.length) {
      requestData.file_ids = selectedChatFiles.value.map(f => f.docId)
    }

    const payload = await streamChatCompletion(requestData, getRequestHeaders(), {
      signal: controller.signal,
      onChunk: (chunk) => {
        streamState.answer += chunk

        patchChatMessage(pendingAssistantMessageId, {
          content: streamState.answer,
          isPending: false,
          isStreaming: true,
          isStopped: false
        })
        scrollChatToBottom()
      }
    }) || {}

    const nextSessionId = payload.session_id || previousSessionId

    if (!nextSessionId) {
      currentSessionId.value = previousSessionId
      historyItems.value = previousHistoryItems
      chatMessages.value = previousMessages
      inputMessage.value = content
      ElMessage.error('后端未返回有效的 session_id')
      return
    }

    currentSessionId.value = nextSessionId

    const answer = streamState.answer || payload.answer || payload.message?.content || '未获取到回答内容'
    patchChatMessage(pendingAssistantMessageId, {
      content: answer,
      isPending: false,
      isStreaming: false,
      isStopped: false,
      turnNo: Number(payload.turn_no || activeHistoryItems.value.length + 1),
      sources: Array.isArray(payload.sources) ? payload.sources : [],
      rewrittenQuery: payload.rewritten_query || null
    })

    patchChatMessage(pendingMerchantMessageId, {
      inputType: payload.input_type || (selectedImage ? 'image' : 'text'),
      ocrText: payload.ocr_text || '',
      imageId: payload.image_id || selectedImage?.imageId || null,
      imageUrl: payload.image_url || selectedImage?.imageUrl || ''
    })

    const nextTurn = {
      turn_id: payload.turn_id || payload.id || payload.turn_no || Date.now(),
      turn_no: Number(payload.turn_no || activeHistoryItems.value.length + 1),
      query: content,
      answer,
      rewritten_query: payload.rewritten_query || null,
      sources: Array.isArray(payload.sources) ? payload.sources : [],
      created_at: now,
      is_active: true,
      input_type: payload.input_type || (selectedImage ? 'image' : 'text'),
      ocr_text: payload.ocr_text || '',
      image_id: payload.image_id || selectedImage?.imageId || null,
      image_url: payload.image_url || selectedImage?.imageUrl || ''
    }

    if (nextSessionId && nextTurn.turn_no && selectedImage) {
      saveTurnImageMeta(nextSessionId, nextTurn.turn_no, {
        imageId: nextTurn.image_id,
        imageUrl: nextTurn.image_url,
        fileName: selectedImage.fileName
      })
    }

    historyItems.value = previousSessionId && previousSessionId === nextSessionId ? previousHistoryItems : []
    appendImmediateTurn(nextTurn)

    await loadSessions({ targetSessionId: nextSessionId })
    await loadSessionRetrievalConfig(nextSessionId)
    await syncHistoryAfterSend(nextSessionId, nextTurn.turn_no)
    selectedChatImages.value = []
    selectedChatFiles.value = []

    showTimeoutStageMessage(payload.timeout_stage)
  } catch (error) {
    if (error?.name === 'AbortError') {
      if (streamState.stoppedByMerchant) {
        patchChatMessage(pendingAssistantMessageId, {
          content: streamState.answer || '已停止生成',
          isPending: false,
          isStreaming: false,
          isStopped: true
        })
        scrollChatToBottom()
      }

      showTimeoutStageMessage(error?.timeout_stage)

      return
    }

    currentSessionId.value = previousSessionId
    historyItems.value = previousHistoryItems
    chatMessages.value = previousMessages
    inputMessage.value = content
    ElMessage.error(getErrorMessage(error, '发送消息失败'))
  } finally {
    if (streamAbortController.value === controller) {
      streamAbortController.value = null
    }

    if (activeStreamState.value === streamState) {
      activeStreamState.value = null
    }

    sending.value = false
  }
}

const renameCurrentSession = async () => {
  if (!currentSessionId.value || !currentSessionMeta.value || renaming.value) return

  try {
    const { value } = await ElMessageBox.prompt('请输入新的会话标题', '修改标题', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputValue: currentSessionMeta.value.title || '',
      inputPlaceholder: '例如：如何提升我店铺在平台上的流量和曝光？',
      inputValidator: (title) => {
        if (!title || !title.trim()) return '标题不能为空'
        if (title.trim().length > 40) return '标题不能超过40个字符'
        return true
      }
    })

    renaming.value = true
    await updateChatSessionTitle(currentSessionId.value, { title: value.trim() }, getRequestHeaders())
    await loadSessions({ targetSessionId: currentSessionId.value })
    ElMessage.success('标题已更新')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(getErrorMessage(error, '修改标题失败'))
    }
  } finally {
    renaming.value = false
  }
}

const removeSession = async (session) => {
  if (!session?.session_id || deletingSessionId.value || sending.value) return

  try {
    await ElMessageBox.confirm('确认删除整个会话吗？删除后该会话将从列表中移除。', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    deletingSessionId.value = session.session_id
    const wasCurrentSession = session.session_id === currentSessionId.value

    await deleteChatSession(session.session_id, getRequestHeaders())

    if (wasCurrentSession) {
      resetDraftConversation()
    }

    await loadSessions({ autoActivateFirst: wasCurrentSession, targetSessionId: wasCurrentSession ? '' : currentSessionId.value })
    ElMessage.success('会话已删除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(getErrorMessage(error, '删除会话失败'))
    }
  } finally {
    deletingSessionId.value = ''
  }
}

const clearCurrentContext = async () => {
  if (!currentSessionId.value || !hasActiveConversation.value || clearing.value) return

  try {
    await ElMessageBox.confirm('确认清空当前会话上下文吗？会话会保留，但 active 回合会被清空。', '提示', {
      confirmButtonText: '确认清空',
      cancelButtonText: '取消',
      type: 'warning'
    })

    clearing.value = true
    const response = await clearChatSessionContext(currentSessionId.value, getRequestHeaders())
    const payload = getPayload(response)

    await loadSessionHistory(currentSessionId.value)
    await loadSessions({ targetSessionId: currentSessionId.value })
    ElMessage.success(`已清空上下文${payload.cleared_turns ? `，共处理 ${payload.cleared_turns} 轮` : ''}`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(getErrorMessage(error, '清空上下文失败'))
    }
  } finally {
    clearing.value = false
  }
}

const rollbackToTurn = async (item) => {
  if (!currentSessionId.value || !item?.turn_no || rollbackingTurnNo.value || sending.value) return

  try {
    await ElMessageBox.confirm(`确认回滚到第 ${item.turn_no} 轮吗？之后的 active 上下文将失效。`, '提示', {
      confirmButtonText: '确认回滚',
      cancelButtonText: '取消',
      type: 'warning'
    })

    rollbackingTurnNo.value = item.turn_no
    await rollbackChatSession(currentSessionId.value, { turn_no: item.turn_no }, getRequestHeaders())
    await loadSessionHistory(currentSessionId.value)
    await loadSessions({ targetSessionId: currentSessionId.value })
    ElMessage.success(`已回滚到第 ${item.turn_no} 轮`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(getErrorMessage(error, '回滚失败'))
    }
  } finally {
    rollbackingTurnNo.value = null
  }
}

watch(chatMessages, () => {
  scrollChatToBottom()
}, { deep: true })

onBeforeUnmount(() => {
  if (streamAbortController.value) {
    streamAbortController.value.abort()
    streamAbortController.value = null
  }

  if (speechRecognition.value) {
    speechShouldKeepListening.value = false
    clearSpeechRestartTimer()
    speechRecognition.value.onstart = null
    speechRecognition.value.onresult = null
    speechRecognition.value.onerror = null
    speechRecognition.value.onend = null
    if (isListening.value) {
      speechRecognition.value.stop()
    }
    speechRecognition.value = null
  }

  removeSelectedImage()
})

onMounted(async () => {
  initSpeechRecognition()

  try {
    await resolveGlobalRetrievalConfig()
  } catch (error) {
    ElMessage.warning(getErrorMessage(error, '读取全局检索参数失败，已使用默认值'))
  }

  await loadSessions({ autoActivateFirst: true })
})

const handleSourcePreview = async (source) => {

  const docId = source.document_id || source.metadata?.document_id
  if (!docId) {
    ElMessage.warning('该文档片段未关联有效的文档ID，无法预览')
    return
  }

  const docName = source.source || '未命名文档'

  try {
    ElMessage.info('正在获取文档，请稍候...')
    const response = await downloadDocument(docId)

    let blobData;
    let contentType;

    if (response instanceof Blob) {
      blobData = response;
      contentType = response.type;
    } else {
      blobData = response.data || response;
      contentType = response.headers?.['content-type'] || blobData.type;
    }

    const ext = docName.split('.').pop().toLowerCase()
    const isPdf = ext === 'pdf'
    const isTextBased =['txt', 'md', 'csv'].includes(ext)

    if (isTextBased) {
      if (!contentType || !contentType.toLowerCase().includes('charset')) {
        contentType = 'text/plain; charset=utf-8';
      }
    }

    const blob = new Blob([blobData], { type: contentType })
    const blobUrl = URL.createObjectURL(blob)

    if (isPdf || isTextBased) {
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
    ElMessage.error('无法获取文件，可能已被删除或服务器出错')
  }
}
</script>

<template>
  <div class="assistant-page assistant-page--merchant">
    <div class="assistant-shell">
      <aside class="assistant-sidebar" v-loading="sessionsLoading">
        <div class="sidebar-header">
          <div>
            <p class="sidebar-kicker">AI Workspace</p>
            <h2>智能助手</h2>
          </div>
          <el-button circle type="primary" @click="startNewConversation">
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>

        <div class="sidebar-section session-section">
          <div class="section-head">
            <span>最近会话</span>
            <span class="section-extra">{{ sessions.length }} 个</span>
          </div>

          <div v-if="sessions.length" class="session-list">
            <div
                v-for="session in sessions"
                :key="session.session_id"
                class="session-card"
                :class="{ active: session.session_id === currentSessionId }"
                role="button"
                tabindex="0"
                @click="activateSession(session)"
                @keydown.enter.prevent="activateSession(session)"
                @keydown.space.prevent="activateSession(session)"
            >
              <div class="session-card-top">
                <span class="session-title">{{ session.title || '未命名会话' }}</span>
                <div class="session-card-actions">
                  <el-tag size="small" effect="plain">{{ session.active_turn_count || 0 }} 轮有效</el-tag>
                  <el-button
                      link
                      type="danger"
                      class="session-delete-button"
                      :loading="deletingSessionId === session.session_id"
                      @click.stop="removeSession(session)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
              <p class="session-preview">更新时间：{{ formatTime(session.updated_at || session.created_at) }}</p>
            </div>
          </div>

          <el-empty v-else description="暂无历史会话" :image-size="72" />
        </div>

        <div class="sidebar-section turn-section">
          <div class="section-head">
            <span>当前历史</span>
            <span class="section-extra">{{ historyItems.length }} 条</span>
          </div>

          <div v-if="sessionTurnList.length" class="turn-list">
            <div
                v-for="item in sessionTurnList"
                :key="item.turn_id"
                class="turn-card"
                :class="{ inactive: item.is_active === false }"
            >
              <div class="turn-card-top">
                <span>第 {{ item.turn_no }} 轮</span>
                <el-tag :type="item.is_active === false ? 'info' : 'success'" size="small">
                  {{ item.is_active === false ? '已失效' : '生效中' }}
                </el-tag>
              </div>

              <p class="turn-query">{{ item.query }}</p>

              <div class="turn-card-bottom">
                <span>{{ formatTime(item.created_at) }}</span>
                <el-button
                    link
                    type="primary"
                    :disabled="item.is_active === false || rollbackingTurnNo === item.turn_no || sending"
                    @click="rollbackToTurn(item)"
                >
                  回滚到此
                </el-button>
              </div>
            </div>
          </div>

          <div v-else class="sidebar-empty-hint">
            选择会话后可查看完整时间线；新会话会在发送首条消息后自动生成。
          </div>
        </div>
      </aside>

      <section class="assistant-main">
        <div class="assistant-topbar">
          <div class="session-summary">
            <h3>{{ currentSessionMeta?.title || '开始一个新的智能对话' }}</h3>
          </div>

          <div class="toolbar-actions">
            <el-popover placement="bottom-end" :width="280" trigger="click" popper-style="padding: 16px; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.08);">
              <template #reference>
                <el-button plain style="border-radius: 8px;">
                  <el-icon><Setting /></el-icon>
                  <span style="margin-left:4px;">对话配置</span>
                </el-button>
              </template>
              
              <div class="config-popover-content">
                <div style="font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 12px;">检索参数配置</div>
                
                <div class="retrieval-config-item" style="margin-bottom: 12px;" v-loading="retrievalConfigLoading && !!currentSessionId">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span class="retrieval-label">检索 Top K</span>
                  </div>
                  <el-input-number
                      v-model="sessionRetrievalConfig.top_k"
                      :min="1" :step="1" size="small" controls-position="right"
                      :disabled="!currentSessionId || sending || retrievalConfigSaving"
                      style="width: 100%"
                  />
                </div>

                <div class="retrieval-config-item" style="margin-bottom: 16px;" v-loading="retrievalConfigLoading && !!currentSessionId">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span class="retrieval-label">相似度阈值</span>
                  </div>
                  <el-input-number
                      v-model="sessionRetrievalConfig.similarity_threshold"
                      :min="0" :max="1" :step="0.01" :precision="2" size="small" controls-position="right"
                      :disabled="!currentSessionId || sending || retrievalConfigSaving"
                      style="width: 100%"
                  />
                </div>

                <div class="retrieval-actions" style="display: flex; justify-content: flex-end; gap: 8px; margin-bottom: 16px;">
                  <el-button
                      plain size="small"
                      :disabled="!currentSessionId || sending"
                      :loading="retrievalConfigSaving"
                      @click="resetSessionRetrievalConfig"
                  >
                    回退全局
                  </el-button>
                  <el-button
                      type="primary" plain size="small"
                      :disabled="!currentSessionId || sending"
                      :loading="retrievalConfigSaving"
                      @click="saveSessionRetrievalConfig"
                  >
                    应用
                  </el-button>
                </div>

                <div style="height: 1px; background: #e5e7eb; margin: 16px -16px;"></div>

                <div style="font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 12px;">会话管理</div>
                
                <div class="session-action-row" style="display: flex; gap: 8px; width: 100%;">
                  <el-button
                      style="flex: 1; margin-left: 0;"
                      plain size="small"
                      :disabled="!currentSessionId"
                      :loading="renaming"
                      @click="renameCurrentSession"
                  >
                    <el-icon><EditPen /></el-icon>
                    修改标题
                  </el-button>

                  <el-button
                      style="flex: 1; margin-left: 0;"
                      type="danger" plain size="small"
                      :disabled="!hasActiveConversation"
                      :loading="clearing"
                      @click="clearCurrentContext"
                  >
                    <el-icon><Delete /></el-icon>
                    清空历史
                  </el-button>
                </div>
              </div>
            </el-popover>
          </div>
        </div>

        <div class="chat-panel">
          <div v-if="chatMessages.length" ref="messageViewport" class="message-list" v-loading="historyLoading && !!currentSessionId">
            <div
                v-for="message in chatMessages"
                :key="message.id"
                class="message-row"
                :class="{
                'is-assistant': message.role === 'assistant',
                'is-user': message.role !== 'assistant'
              }"
            >
              <div
                  class="message-avatar"
                  :class="{
                  'assistant-avatar': message.role === 'assistant',
                  'user-avatar': message.role !== 'assistant'
                }"
              >
                <el-icon v-if="message.role === 'assistant'"><ChatLineRound /></el-icon>
                <el-icon v-else><User /></el-icon>
              </div>

              <div class="message-body">
                <div class="message-meta">
                  <span class="message-author">
                    {{ message.role === 'assistant' ? '智能助手' : currentUserName }}
                  </span>
                  <span v-if="message.turnNo">第 {{ message.turnNo }} 轮</span>
                  <span>{{ formatTime(message.createdAt) }}</span>
                </div>

                <div
                    class="message-bubble"
                    :class="{
                    'assistant-bubble': message.role === 'assistant',
                    'user-bubble': message.role !== 'assistant',
                    'pending-bubble': message.isPending
                  }"
                >

                  <template v-if="message.role === 'assistant'">
                    <MarkdownRenderer :content="message.content" />
                  </template>
                  <template v-else>
                    <div class="message-text">{{ message.content }}</div>
                    <div v-if="message.imageId" class="message-image-attachment" @click="handlePreviewMessageImage(message)">
                      <el-icon><Picture /></el-icon>
                      <span class="attachment-name">{{ message.fileName || extractFileName(message.imageUrl, message.imageId) }}</span>
                    </div>
                  </template>
                </div>

                <details v-if="message.role === 'assistant' && message.rewrittenQuery" class="collapsible-panel panel-purple">
                  <summary>
                    <div class="summary-content">
                      <el-icon><EditPen /></el-icon>
                      <span class="debug-label">问题改写</span>
                    </div>
                  </summary>
                  <div class="collapsible-content">
                    {{ message.rewrittenQuery }}
                  </div>
                </details>

                <details
                  v-if="message.role === 'assistant' && message.sources && message.sources.length"
                  class="collapsible-panel panel-blue"
                >
                  <summary>
                    <div class="summary-content">
                      <el-icon><Document /></el-icon>
                      <span class="sources-title-text">证据来源 ({{ message.sources.length }})</span>
                    </div>
                  </summary>
                  <div class="collapsible-content sources-list">
                    <div
                      v-for="(source, index) in message.sources"
                      :key="`${message.id}-source-${index}`"
                      class="source-card"
                    >
                      <div class="source-card-top">
                        <span
                            class="source-name clickable"
                            :title="'点击预览: ' + formatSourceDisplayName(source)"
                            @click="handleSourcePreview(source)"
                        >
                          {{ formatSourceDisplayName(source) }}
                        </span>
                        <el-tag v-if="source.score != null" type="success" effect="plain" size="small">
                          相似度 {{ Number(source.score).toFixed(4) }}
                        </el-tag>
                      </div>
                      <div class="source-content">{{ source.content || '暂无片段内容' }}</div>
                    </div>
                  </div>
                </details>

                <div v-if="message.role === 'assistant'" class="rating-panel">
                  <el-button
                      type="primary"
                      plain
                      size="small"
                      :class="{ 'active': message.rating === 1 }"
                      :disabled="message.rating === -1"
                      @click="handleRating(message, 1)"
                  >
                    赞
                  </el-button>
                  <el-button
                      type="danger"
                      plain
                      size="small"
                      :class="{ 'active': message.rating === -1 }"
                      :disabled="message.rating === 1"
                      @click="handleRating(message, -1)"
                  >
                    踩
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="empty-chat-state">
            <div class="empty-chat-icon">
              <el-icon><Promotion /></el-icon>
            </div>
          </div>

          <div class="composer-wrapper">
            <div class="quick-question-panel">
              <div class="quick-question-list">
                <el-button
                    v-for="question in QUICK_QUESTION_TEMPLATES"
                    :key="question"
                    class="quick-question-button"
                    plain
                    :disabled="sending"
                    @click="sendTemplateQuestion(question)"
                >
                  {{ question }}
                </el-button>
              </div>
            </div>

            <div class="composer-panel">
              <input
                ref="imageUploadInputRef"
                type="file"
                accept=".jpg,.jpeg,.png,.webp,.bmp,image/jpeg,image/png,image/webp,image/bmp"
                class="chat-image-input"
                @change="handleSelectChatImage"
              />

              <input
                ref="fileUploadInputRef"
                type="file"
                accept=".csv,.xlsx,.xls,.txt,.md,.pdf,.docx"
                class="chat-image-input"
                @change="handleSelectDataFile"
              />

              <div v-if="selectedChatImages.length || selectedChatFiles.length" class="chat-image-list-panel">
                <div class="chat-image-list">
                  <div
                    v-for="image in selectedChatImages"
                    :key="image.imageId"
                    class="chat-image-chip"
                  >
                    <span class="chat-image-name" :title="image.fileName" @click="window.open(image.imageUrl, '_blank')">{{ image.fileName }}</span>
                    <el-button
                      link
                      type="danger"
                      :disabled="sending || imageUploading"
                      @click="removeSelectedImage"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>

                  <div
                    v-for="(file, idx) in selectedChatFiles"
                    :key="file.docId"
                    class="chat-image-chip"
                  >
                    <span class="chat-image-name" :title="file.fileName"> {{ file.fileName }}</span>
                    <el-button
                      link
                      type="danger"
                      :disabled="sending || fileUploading"
                      @click="removeSelectedFile(idx)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>

              <el-input
                  v-model="inputMessage"
                  type="textarea"
                  resize="none"
                  :autosize="{ minRows: 1, maxRows: 6 }"
                  placeholder="请输入你的问题..."
                  @keydown.enter.exact.prevent="sendMessage"
              />

              <div class="composer-footer">
                <div class="composer-hints">
                  <span>Enter 发送</span>
                  <span>Shift + Enter 换行</span>
                </div>

                <div class="composer-actions">
                  <el-button
                    circle
                    plain
                    :type="(speechShouldKeepListening || isListening) ? 'success' : 'info'"
                    :disabled="sending || !speechRecognitionSupported"
                    :title="speechRecognitionSupported ? ((speechShouldKeepListening || isListening) ? '停止语音输入' : '开始语音输入') : '当前浏览器不支持语音输入'"
                    @click="toggleSpeechInput"
                  >
                    <el-icon><Microphone /></el-icon>
                  </el-button>

                  <el-button
                    circle
                    plain
                    type="info"
                    :loading="imageUploading"
                    :disabled="sending || imageUploading || selectedChatImages.length >= MAX_CHAT_IMAGE_COUNT"
                    title="上传图片"
                    @click="triggerImagePicker"
                  >
                    <el-icon><Picture /></el-icon>
                  </el-button>

                  <el-button
                    circle
                    plain
                    type="info"
                    :loading="fileUploading"
                    :disabled="sending || fileUploading"
                    title="上传数据文件"
                    @click="triggerFilePicker"
                  >
                    <el-icon><DocumentAdd /></el-icon>
                  </el-button>

                  <el-button v-if="sending" type="danger" plain @click="stopGeneration">
                    <el-icon><Delete /></el-icon>
                    停止生成
                  </el-button>

                  <el-button v-else type="primary" :disabled="(!inputMessage.trim() && !selectedChatImages.length && !selectedChatFiles.length) || speechShouldKeepListening || isListening || imageUploading || fileUploading" @click="sendMessage">
                    <el-icon><Promotion /></el-icon>
                    发送
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <el-dialog v-model="imagePreviewVisible" :title="previewImageName" width="50%" center align-center destroy-on-close>
      <div v-loading="previewImageLoading" style="min-height: 200px; display: flex; align-items: center; justify-content: center;">
        <img v-if="previewImageUrl" :src="previewImageUrl" style="max-width: 100%; max-height: 65vh; display: block; margin: 0 auto; border-radius: 8px;" alt="Image Preview" />
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.assistant-page {
  height: calc(100vh - 100px);
  min-height: 680px;
}

.assistant-shell {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  height: 100%;
  min-height: 0;
  background-color: transparent;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  box-sizing: border-box;
}

.assistant-sidebar {
  display: flex;
  flex-direction: column;
  padding: 20px;
  background-color: #ffffff;
  border-right: 1px solid #e5e7eb;
  min-height: 0;
  overflow: hidden;
}

.assistant-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(16px);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-shrink: 0;
}

.sidebar-kicker {
  margin: 0 0 4px;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #9ca3af;
}

.sidebar-header h2 {
  margin: 0;
  color: #111827;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.sidebar-section + .sidebar-section {
  margin-top: 24px;
}

.session-section,
.turn-section {
  flex: 1 1 0;
}

.turn-section {
  min-height: 0;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  color: #4b5563;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.section-extra {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 400;
}

.session-list,
.turn-list {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  gap: 8px;
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.session-list::-webkit-scrollbar,
.turn-list::-webkit-scrollbar {
  display: none;
}

.turn-list {
  flex: 1;
}

.session-card {
  padding: 12px 14px;
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s ease;
  text-align: left;
}

.turn-card {
  padding: 12px 14px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
  text-align: left;
}

.session-card:hover {
  background-color: #f3f4f6;
}

.session-card.active {
  background-color: #eef2ff;
  border-color: #eef2ff;
}

.session-card-top,
.turn-card-top,
.source-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.session-card-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.session-delete-button {
  padding: 0;
}

.session-title,
.source-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-name.clickable {
  color: #4f46e5;
  cursor: pointer;
  text-decoration: underline;
  transition: color 0.3s ease;
}

.source-name.clickable:hover {
  color: #6366f1;
}

.session-preview,
.turn-query,
.source-content {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.5;
}

.turn-card-bottom {
  margin-top: 10px;
  color: #9ca3af;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.turn-card.inactive {
  opacity: 0.72;
}

.sidebar-empty-hint {
  color: #9ca3af;
  font-size: 12px;
  line-height: 1.6;
  padding: 16px 4px;
  text-align: center;
}

.assistant-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  flex-shrink: 0;
  gap: 16px;
  z-index: 10;
}

.session-summary {
  min-width: 0;
  flex: 1;
}

.topbar-kicker {
  margin: 0 0 4px;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #9ca3af;
}

.assistant-topbar h3 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  font-family: "Avenir Next", "Avenir", "Nunito", -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  letter-spacing: 0.02em;
  background: linear-gradient(135deg, #4f46e5 0%, #d946ef 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.topbar-subtitle {
  color: #6b7280;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.session-id-label {
  flex-shrink: 0;
}

.session-id-value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.toolbar-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.retrieval-config-group {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f9fafb;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #f3f4f6;
}

.retrieval-config-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.retrieval-label {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
}

.retrieval-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.session-action-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  align-items: center;
  position: relative;
}

.message-list {
  width: 90%;
  flex: 1;
  overflow-y: auto;
  padding: 24px 40px 0 40px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.message-list::-webkit-scrollbar {
  display: none;
}

.message-row {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
  width: 100%;
}

.message-row.is-user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  flex-shrink: 0;
}

.assistant-avatar {
  background: #10a37f;
}

.user-avatar {
  background: #f3f4f6;
  color: #6b7280;
}

.message-body {
  min-width: 0;
  max-width: calc(100% - 100px);
}

.message-row.is-user .message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
  color: #9ca3af;
}

.message-row.is-user .message-meta {
  justify-content: flex-end;
}

.message-author {
  color: #111827;
  font-weight: 600;
}

.message-bubble {
  line-height: 1.7;
  word-break: break-word;
  font-size: 15px;
  color: #374151;
}

.assistant-bubble {
  background: transparent;
  padding: 0;
}

.user-bubble {
  background: #f4f4f5;
  padding: 12px 18px;
  border-radius: 18px;
  border-top-right-radius: 4px;
  color: #111827;
}

.pending-bubble {
  opacity: 0.6;
}

.message-text {
  white-space: pre-wrap;
}

.message-image-attachment {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 8px 14px;
  background: #f9fafb;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.25s ease;
  font-size: 13px;
  color: #4b5563;
}

.message-image-attachment:hover {
  background: #f3f4f6;
}

.attachment-name {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.collapsible-panel {
  margin-top: 12px;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.collapsible-panel summary {
  cursor: pointer;
  font-weight: 500;
  color: #4b5563;
  outline: none;
  display: list-item;
}

.collapsible-panel summary::marker {
  color: #4b5563;
}

.summary-content {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  vertical-align: middle;
}

.debug-label, .sources-title-text {
  font-weight: 500;
}

.collapsible-content {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e5e7eb;
  color: #374151;
}

.rating-panel {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.rating-panel .el-button.active {
  background-color: var(--el-button-bg-color);
  border-color: var(--el-button-border-color);
  color: var(--el-button-text-color);
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-card {
  padding: 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.composer-wrapper {
  width: 100%;
  padding: 0 36px 24px 36px;
  box-sizing: border-box;
}

.quick-question-panel {
  margin-bottom: 12px;
  display: flex;
  justify-content: flex-start;
}

.quick-question-list {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  align-items: center;
}

.quick-question-button {
  border-radius: 999px;
  font-size: 13px;
  padding: 8px 16px;
  color: #4f46e5;
  border-color: #e0e7ff;
  background: #eef2ff;
  margin: 0;
  flex-shrink: 0;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.08);
}

.quick-question-button:hover {
  background: #4f46e5;
  color: #fff;
  border-color: #4f46e5;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
}

.composer-panel {
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  padding: 14px 18px;
  position: relative;
  transition: all 0.25s ease;
}

.composer-panel:focus-within {
  border-color: #a5b4fc;
}

.composer-panel :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding: 0;
  font-size: 15px;
  line-height: 1.5;
  background: transparent;
  color: #111827;
}

.composer-panel :deep(.el-textarea__inner:focus) {
  box-shadow: none;
  background: transparent;
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.composer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.composer-hints {
  font-size: 11px;
  color: #9ca3af;
  display: flex;
  gap: 12px;
}

.chat-image-input { display: none; }

.chat-image-list-panel {
  margin-bottom: 8px;
}

.chat-image-list {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.chat-image-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #f3f4f6;
  border-radius: 8px;
  font-size: 12px;
}

.chat-image-name {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #374151;
  cursor: pointer;
}

.empty-chat-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.empty-chat-icon {
  font-size: 48px;
  color: #e5e7eb;
  margin-bottom: 16px;
}

@media (max-width: 1200px) {
  .assistant-shell {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .composer-wrapper {
    padding: 0 16px 16px;
  }
  .message-list {
    padding: 16px 16px 0;
  }
}

.assistant-page--merchant {
  --assistant-bg: linear-gradient(180deg, #f6faf8 0%, #edf5f2 100%);
  --assistant-surface: rgba(255, 255, 255, 0.92);
  --assistant-border: rgba(190, 214, 205, 0.88);
  --assistant-muted: #6c7f79;
  --assistant-text: #16352d;
  --assistant-accent: #2f7d6b;
  --assistant-accent-soft: rgba(47, 125, 107, 0.1);
  --assistant-topbar-start: #24453f;
  --assistant-topbar-end: #2f6b5f;
  --assistant-user-bubble: #e3f1ed;
  background: transparent;
}

.assistant-page--merchant .assistant-shell {
  border-radius: 24px;
  box-shadow: none;
  background: transparent;
}

.assistant-page--merchant .assistant-sidebar {
  padding: 18px;
  background: linear-gradient(180deg, rgba(246, 251, 249, 0.98) 0%, rgba(238, 246, 243, 0.98) 100%);
  border-right: 1px solid var(--assistant-border);
}

.assistant-page--merchant .assistant-main {
  background: transparent;
  backdrop-filter: none;
}

.assistant-page--merchant .sidebar-header {
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(190, 214, 205, 0.55);
}

.assistant-page--merchant .assistant-sidebar .sidebar-kicker {
  color: #7a9189;
  letter-spacing: 0.16em;
}

.assistant-page--merchant .assistant-topbar {
  padding: 18px 24px;
  border-bottom: none;
  background: linear-gradient(135deg, var(--assistant-topbar-start) 0%, var(--assistant-topbar-end) 100%);
}

.assistant-page--merchant .topbar-kicker {
  color: rgba(235, 248, 243, 0.72);
}

.assistant-page--merchant .assistant-topbar h3 {
  color: #f8fffc;
  background: none;
  -webkit-text-fill-color: initial;
}

.assistant-page--merchant .topbar-subtitle,
.assistant-page--merchant .session-id-label,
.assistant-page--merchant .session-id-value {
  color: rgba(235, 248, 243, 0.76);
}

.assistant-page--merchant .toolbar-actions {
  gap: 8px;
}

.assistant-page--merchant .toolbar-actions :deep(.el-button),
.assistant-page--merchant .session-action-row :deep(.el-button) {
  border-radius: 12px;
}

.assistant-page--merchant .toolbar-actions :deep(.el-button--primary),
.assistant-page--merchant .composer-actions :deep(.el-button--primary) {
  background: var(--assistant-accent);
  border-color: var(--assistant-accent);
  box-shadow: none;
}

.assistant-page--merchant .toolbar-actions :deep(.el-button),
.assistant-page--merchant .composer-actions :deep(.el-button),
.assistant-page--merchant .quick-question-button,
.assistant-page--merchant .session-card,
.assistant-page--merchant .turn-card {
  box-shadow: none !important;
}

.assistant-page--merchant .session-card,
.assistant-page--merchant .turn-card,
.assistant-page--merchant .source-card,
.assistant-page--merchant .collapsible-panel {
  border-radius: 14px;
  border: 1px solid transparent;
  background: transparent;
  box-shadow: none;
}

.assistant-page--merchant .session-card:hover,
.assistant-page--merchant .turn-card:hover {
  background: rgba(47, 125, 107, 0.06);
}

.assistant-page--merchant .session-card.active,
.assistant-page--merchant .turn-card,
.assistant-page--merchant .source-card,
.assistant-page--merchant .collapsible-panel {
  background: rgba(255, 255, 255, 0.66);
  border-color: rgba(190, 214, 205, 0.7);
}

.assistant-page--merchant .chat-panel {
  align-items: stretch;
}

.assistant-page--merchant .message-list {
  width: 100%;
  padding: 28px 28px 0;
}

.assistant-page--merchant .message-row {
  margin-bottom: 24px;
}

.assistant-page--merchant .user-bubble {
  background: var(--assistant-user-bubble);
  border-top-right-radius: 6px;
}

.assistant-page--merchant .message-image-attachment,
.assistant-page--merchant .chat-image-chip,
.assistant-page--merchant .retrieval-config-group {
  background: rgba(255, 255, 255, 0.75);
  border-color: rgba(190, 214, 205, 0.7);
}

.assistant-page--merchant .quick-question-button {
  color: #2f7d6b;
  border-color: rgba(47, 125, 107, 0.2);
  background: rgba(47, 125, 107, 0.08);
}

.assistant-page--merchant .quick-question-button:hover {
  background: #2f7d6b;
  color: #ffffff;
  border-color: #2f7d6b;
  box-shadow: none;
}

.assistant-page--merchant .empty-chat-state {
  padding: 64px 28px 40px;
}

.assistant-page--merchant .empty-chat-icon {
  color: var(--assistant-accent);
}

.assistant-page--merchant .composer-wrapper {
  width: 100%;
  padding: 0 24px 22px;
}

.assistant-page--merchant .composer-panel {
  border-radius: 22px;
  border: 1px solid rgba(190, 214, 205, 0.86);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: none;
}

.assistant-page--merchant .composer-panel:focus-within {
  border-color: rgba(47, 125, 107, 0.56);
  box-shadow: none;
}

.assistant-page--merchant .composer-footer {
  border-top: none;
}

.assistant-page--merchant .composer-hints,
.assistant-page--merchant .session-preview,
.assistant-page--merchant .turn-query,
.assistant-page--merchant .source-content,
.assistant-page--merchant .message-meta,
.assistant-page--merchant .sidebar-empty-hint {
  color: var(--assistant-muted);
}

.assistant-page--merchant .rating-panel :deep(.el-button) {
  min-width: 44px;
  height: 36px;
  padding: 0 10px;
  font-size: 14px;
  border-radius: 999px;
  box-shadow: none;
}

.assistant-page--merchant .rating-panel :deep(.el-button:first-child) {
  color: #2f7d6b;
  border-color: rgba(47, 125, 107, 0.28);
  background: rgba(47, 125, 107, 0.1);
}

.assistant-page--merchant .rating-panel :deep(.el-button:last-child) {
  color: #2d6f53;
  border-color: rgba(45, 111, 83, 0.3);
  background: rgba(45, 111, 83, 0.1);
}

.assistant-page--merchant .rating-panel :deep(.el-button.active) {
  color: #ffffff !important;
  border-color: transparent;
}

.assistant-page--merchant .rating-panel :deep(.el-button.active span) {
  color: #ffffff !important;
}

.assistant-page--merchant .rating-panel :deep(.el-button:first-child.active) {
  background: #2f7d6b;
}

.assistant-page--merchant .rating-panel :deep(.el-button:last-child.active) {
  background: #2d6f53;
}

.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain) {
  background: #2f7d6b;
  border-color: #2f7d6b;
  color: #ffffff !important;
  box-shadow: none;
  --el-button-text-color: #ffffff !important;
  --el-button-hover-text-color: #ffffff !important;
  --el-button-active-text-color: #ffffff !important;
}

.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain span) {
  color: #ffffff !important;
}

.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain:hover),
.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain:focus) {
  background: #286a5a;
  border-color: #286a5a;
  color: #ffffff !important;
  box-shadow: none;
  --el-button-text-color: #ffffff !important;
  --el-button-hover-text-color: #ffffff !important;
  --el-button-active-text-color: #ffffff !important;
}

.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain:hover span),
.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain:focus span),
.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain:active span) {
  color: #ffffff !important;
}

.assistant-page--merchant :deep(.el-button),
.assistant-page--merchant :deep(.el-button:hover),
.assistant-page--merchant :deep(.el-button:focus),
.assistant-page--merchant :deep(.el-button:active) {
  box-shadow: none !important;
}

.assistant-page--merchant .session-title {
  color: #226b5b;
}

.assistant-page--merchant .quick-question-button {
  color: #226b5b;
  border-color: rgba(34, 107, 91, 0.22);
  background: rgba(34, 107, 91, 0.08);
}

.assistant-page--merchant .quick-question-button:hover,
.assistant-page--merchant .quick-question-button:focus {
  color: #ffffff;
  border-color: #226b5b;
  background: #226b5b;
  box-shadow: none !important;
}

.assistant-page--merchant .rating-panel :deep(.el-button:first-child) {
  background: #e8f5ef !important;
  border-color: rgba(34, 107, 91, 0.28) !important;
  color: #226b5b !important;
  box-shadow: none !important;
  --el-button-text-color: #226b5b !important;
  --el-button-hover-text-color: #ffffff !important;
  --el-button-active-text-color: #ffffff !important;
}

.assistant-page--merchant .rating-panel :deep(.el-button:first-child:hover),
.assistant-page--merchant .rating-panel :deep(.el-button:first-child:focus),
.assistant-page--merchant .rating-panel :deep(.el-button:first-child.active) {
  background: #2f7d6b !important;
  border-color: #2f7d6b !important;
  color: #ffffff !important;
  box-shadow: none !important;
}

.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain) {
  background: #dbeafe !important;
  border-color: #93c5fd !important;
  color: #1d4ed8 !important;
  box-shadow: none !important;
  --el-button-text-color: #1d4ed8 !important;
  --el-button-hover-text-color: #ffffff !important;
  --el-button-active-text-color: #ffffff !important;
}

.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain:hover),
.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain:focus),
.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain:active) {
  background: #2563eb !important;
  border-color: #2563eb !important;
  color: #ffffff !important;
  box-shadow: none !important;
}

.assistant-page--merchant .rating-panel :deep(.el-button:first-child span),
.assistant-page--merchant .config-popover-content :deep(.el-button--primary.is-plain span) {
  color: inherit !important;
}
</style>






