<template>
	<div class="pandas-analyzer-page">
		<el-card shadow="never" class="file-list-card">
					<template #header>
						<div class="card-header card-header-with-filter">
							<div class="header-title-wrap">
								<span>文件列表</span>
								<el-radio-group v-model="statusFilter" size="small" @change="loadDocuments">
									<el-radio-button label="all">全部</el-radio-button>
									<el-radio-button label="pending">待审核</el-radio-button>
									<el-radio-button label="approved">已通过</el-radio-button>
									<el-radio-button label="rejected">已驳回</el-radio-button>
								</el-radio-group>
							</div>
							<el-button type="primary" size="small" :loading="loading" @click="loadDocuments">刷新</el-button>
						</div>
					</template>

					<el-table
						:data="documentList"
						v-loading="loading"
						border
						stripe
						height="360"
					>
						<el-table-column prop="doc_name" label="文件名" min-width="160" show-overflow-tooltip />
						<el-table-column label="状态" width="90" align="center">
							<template #default="scope">
								<span>{{ formatStatus(scope.row.status) }}</span>
							</template>
						</el-table-column>
						<el-table-column label="操作" width="90" align="center" fixed="right">
							<template #default="scope">
								<el-button size="small" type="primary" link @click.stop="selectFile(scope.row)">选择</el-button>
							</template>
						</el-table-column>
					</el-table>

					<div class="pagination-wrap" v-if="total > pageSize">
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

		<el-card shadow="never" class="analysis-card">
					<template #header>
						<div class="card-header">
							<span>数据智能分析</span>
							<el-tag v-if="selectedDocument" type="success" size="small">当前文件：{{ selectedDocument.doc_name }}</el-tag>
							<el-tag v-else type="info" size="small">请先选择文件</el-tag>
						</div>
					</template>

					<div class="analysis-input">
						<el-input
							v-model="analysisQuery"
							placeholder="输入自然语言，例如：按类别计算平均价格"
							@keyup.enter="handleAnalysis"
							clearable
						>
							<template #append>
								<el-button :loading="analyzing" @click="handleAnalysis">分析</el-button>
							</template>
						</el-input>
					</div>

					<div class="analysis-result-container" v-loading="analyzing">
						<el-scrollbar max-height="580">
							<div v-if="analysisResult.data || analysisResult.chart || analysisResult.code || analysisResult.sandboxOutput || analysisResult.summary" class="result-panel">
								<div v-if="analysisResult.chart" class="result-chart">
									<el-image
										v-if="isBase64Chart(analysisResult.chart)"
										:src="'data:image/png;base64,' + analysisResult.chart"
										fit="contain"
									/>

									<div v-else-if="isBarChart(analysisResult.chart)" class="bar-chart">
										<div
											v-for="(label, idx) in analysisResult.chart.labels"
											:key="`${label}-${idx}`"
											class="bar-row"
										>
											<div class="bar-label">{{ label }}</div>
											<div class="bar-track">
												<div
													class="bar-fill"
													:style="{ width: getBarWidth(analysisResult.chart.values[idx], analysisResult.chart.values) }"
												/>
											</div>
											<div class="bar-value">{{ analysisResult.chart.values[idx] }}</div>
										</div>
									</div>

									<el-table
										v-else-if="isTableChart(analysisResult.chart)"
										:data="analysisResult.chart.data"
										size="small"
										stripe
										border
									>
										<el-table-column
											v-for="(val, key) in analysisResult.chart.data[0]"
											:key="key"
											:prop="key"
											:label="key"
										/>
									</el-table>
								</div>

								<el-table
									v-if="Array.isArray(analysisResult.data) && analysisResult.data.length > 0"
									:data="analysisResult.data"
									size="small"
									stripe
									border
								>
									<el-table-column
										v-for="(val, key) in analysisResult.data[0]"
										:key="key"
										:prop="key"
										:label="key"
									/>
								</el-table>

								<el-table
									v-else-if="isPlainObject(analysisResult.data)"
									:data="dictToRows(analysisResult.data)"
									size="small"
									stripe
									border
								>
									<el-table-column prop="key" label="字段" min-width="180" show-overflow-tooltip />
									<el-table-column prop="value" label="值" min-width="220" show-overflow-tooltip />
								</el-table>

								<div v-else-if="typeof analysisResult.data === 'string'" class="answer-card">
									<MarkdownRenderer :content="analysisResult.data" />
								</div>

								<pre v-else-if="analysisResult.data" class="result-text">{{ formatResultText(analysisResult.data) }}</pre>

								<div v-if="analysisResult.summary" class="result-summary">
									<el-tag type="info" effect="light" class="summary-tag">执行说明</el-tag>
									<span class="summary-text">{{ analysisResult.summary }}</span>
								</div>

								<pre
									v-if="!analysisResult.data && !analysisResult.chart && analysisResult.sandboxOutput"
									class="result-text sandbox-preview"
								>{{ analysisResult.sandboxOutput }}</pre>

								<el-collapse v-if="analysisResult.code || analysisResult.sandboxOutput" class="code-collapse" style="margin-top: 12px;">
									<el-collapse-item v-if="analysisResult.code" title="查看 Agent 生成代码" name="1">
										<pre class="code-block">{{ analysisResult.code }}</pre>
									</el-collapse-item>
									<el-collapse-item v-if="analysisResult.sandboxOutput" title="查看运行日志" name="2">
										<pre class="code-block">{{ analysisResult.sandboxOutput }}</pre>
									</el-collapse-item>
								</el-collapse>
							</div>

							<el-empty v-else description="请先选择文件并输入分析指令" :image-size="60" />
						</el-scrollbar>
					</div>
		</el-card>
	</div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import { searchDocuments, getDocumentDetail, previewDocument } from '@/api/documentWorkbench'
import { analyzePandasData } from '@/api/newDocumentWorkbench'

export default {
	name: 'PandasAnalyzer',
	components: {
		MarkdownRenderer
	},
	setup() {
		const loading = ref(false)
		const documentList = ref([])
		const selectedDocument = ref(null)
		const total = ref(0)
		const currentPage = ref(1)
		const pageSize = ref(20)
		const statusFilter = ref('all')

		const analysisQuery = ref('')
		const analyzing = ref(false)
		const analysisResult = ref({ data: null, chart: null, code: '', sandboxOutput: '', summary: '' })

		const loadDocuments = async () => {
			loading.value = true
			try {
				const query = {
					page: currentPage.value,
					page_size: pageSize.value
				}
				if (statusFilter.value !== 'all') {
					query.status = statusFilter.value
				}

				const res = await searchDocuments(query)
				const data = res?.data || res || {}
				const items = Array.isArray(data.items) ? data.items : []
				documentList.value = items.filter(item => {
					const status = String(item?.status || '').toLowerCase()
					if (status === 'deprecated') return false
					if (statusFilter.value === 'all') {
						return ['pending', 'approved', 'rejected'].includes(status)
					}
					return status === statusFilter.value
				})
				total.value = documentList.value.length
			} catch (error) {
				console.error('加载文件列表失败:', error)
				ElMessage.error('加载文件列表失败')
			} finally {
				loading.value = false
			}
		}

		const handleCurrentChange = async (row) => {
			selectedDocument.value = row || null
			analysisResult.value = { data: null, chart: null, code: '', sandboxOutput: '', summary: '' }

			if (!row) {
				return
			}

			try {
				const detail = await getDocumentDetail(row.doc_id || row.id)
				const filePath = detail?.file_path || detail?.data?.file_path || detail?.data?.document?.file_path
				if (filePath) {
					selectedDocument.value.file_path = filePath
				}
			} catch (error) {
				console.error('获取文件详情失败:', error)
			}
		}

		const selectFile = async (row) => {
			await handleCurrentChange(row)
			if (row?.doc_name) {
				ElMessage.success(`已选择文件：${row.doc_name}`)
			}
		}

		const handleAnalysis = async () => {
			if (!selectedDocument.value) {
				ElMessage.warning('请先选择文件')
				return
			}

			if (!analysisQuery.value.trim()) {
				ElMessage.warning('请输入分析指令')
				return
			}

			analyzing.value = true
			try {
				const datasetRef =
					selectedDocument.value.file_path ||
					selectedDocument.value.doc_id ||
					selectedDocument.value.id

				const res = await analyzePandasData(String(datasetRef), analysisQuery.value)

				const isAnalysisEnvelope = (value) => {
					return !!value &&
						typeof value === 'object' &&
						(
							'status' in value ||
							'generated_code' in value ||
							'chart_data' in value ||
							'sandbox_output' in value ||
							'text_summary' in value
						)
				}

				const payload = isAnalysisEnvelope(res)
					? res
					: (isAnalysisEnvelope(res?.data) ? res.data : { data: res })

				analysisResult.value = {
					data: payload?.data ?? null,
					chart: payload?.chart_data ?? payload?.chart ?? null,
					code: payload?.generated_code ?? payload?.code ?? '',
					sandboxOutput: payload?.sandbox_output ?? payload?.sandboxOutput ?? '',
					summary: payload?.text_summary ?? payload?.summary ?? ''
				}

				ElMessage.success('分析完成')
			} catch (error) {
				console.error('分析执行失败:', error)
				const detail = error?.response?.data?.detail
				ElMessage.error(detail ? `分析执行失败: ${detail}` : '分析执行失败')
			} finally {
				analyzing.value = false
			}
		}

		const isBase64Chart = (chart) => typeof chart === 'string' && chart.trim().length > 0

		const isBarChart = (chart) => {
			return !!chart &&
				typeof chart === 'object' &&
				chart.type === 'bar' &&
				Array.isArray(chart.labels) &&
				Array.isArray(chart.values)
		}

		const isTableChart = (chart) => {
			return !!chart &&
				typeof chart === 'object' &&
				chart.type === 'table' &&
				Array.isArray(chart.data) &&
				chart.data.length > 0
		}

		const getBarWidth = (value, values) => {
			const nums = (values || []).map(v => Number(v)).filter(v => Number.isFinite(v))
			const max = nums.length ? Math.max(...nums) : 0
			const current = Number(value)
			if (!Number.isFinite(current) || max <= 0) return '0%'
			return `${Math.max(3, (current / max) * 100)}%`
		}

		const isPlainObject = (value) => {
			return Object.prototype.toString.call(value) === '[object Object]'
		}

		const dictToRows = (value) => {
			if (!isPlainObject(value)) return []
			return Object.entries(value).map(([key, raw]) => {
				let formatted = ''
				if (raw == null) {
					formatted = ''
				} else if (typeof raw === 'object') {
					try {
						formatted = JSON.stringify(raw, null, 2)
					} catch (e) {
						formatted = String(raw)
					}
				} else {
					formatted = String(raw)
				}

				return {
					key,
					value: formatted
				}
			})
		}

		const formatResultText = (value) => {
			if (value == null) return ''
			if (typeof value === 'string') return value
			try {
				return JSON.stringify(value, null, 2)
			} catch (e) {
				return String(value)
			}
		}

		const formatStatus = (status) => {
			const map = {
				pending: '待审核',
				approved: '已通过',
				rejected: '已驳回'
			}
			return map[String(status || '').toLowerCase()] || String(status || '-')
		}

		const formatTime = (value) => {
			if (!value) return '刚刚'
			const date = new Date(value)
			if (Number.isNaN(date.getTime())) return String(value)
			return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
		}

		onMounted(() => {
			loadDocuments()
		})

		return {
			loading,
			documentList,
			selectedDocument,
			total,
			currentPage,
			pageSize,
			statusFilter,
			analysisQuery,
			analyzing,
			analysisResult,
			loadDocuments,
			handleCurrentChange,
			selectFile,
			handleAnalysis,
			isBase64Chart,
			isBarChart,
			isTableChart,
			getBarWidth,
			isPlainObject,
			dictToRows,
			formatResultText,
			formatStatus,
			formatTime
		}
	}
}
</script>

<style scoped>
  .pandas-analyzer-page {
	display: flex;
	flex-direction: column;
	gap: 24px;
  }
  
  .card-header {
  	display: flex;
  	align-items: center;
  	justify-content: space-between;
  	gap: 10px;
  	font-weight: 700;
  	color: var(--rv-text);
  }

.card-header-with-filter {
	align-items: flex-start;
}

.header-title-wrap {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 8px;
}

  .file-list-card,
  .analysis-card {
  	border-radius: 28px;
  	border: 1px solid rgba(70, 85, 116, 0.08);
  	background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 253, 0.97));
  	box-shadow: 0 12px 26px rgba(18, 28, 45, 0.05);
  }
  
  .file-list-card {
  	margin-bottom: 0;
  }

  .file-list-card :deep(.el-card__header),
  .analysis-card :deep(.el-card__header) {
  	border-bottom: 1px solid rgba(125, 138, 164, 0.12);
  }

  .file-list-card :deep(.el-card__body),
  .analysis-card :deep(.el-card__body) {
  	padding: 24px;
  }
  
  .analysis-input {
  	margin-bottom: 16px;
  }
  
  .analysis-result-container {
  	border: 1px solid rgba(72, 88, 117, 0.08);
  	border-radius: 16px;
  	padding: 14px;
  	min-height: 500px;
  	background: linear-gradient(180deg, rgba(247, 249, 252, 0.92), rgba(255, 255, 255, 0.96));
  }

.result-panel {
	display: flex;
	flex-direction: column;
	gap: 12px;
}

  .result-chart {
  	background: #f8f9fa;
  	padding: 12px;
  	border-radius: 14px;
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
  	font-family: Consolas, monospace;
  	font-size: 13px;
  	color: #333;
  	white-space: pre-wrap;
  	word-wrap: break-word;
  	background: #f4f4f5;
  	padding: 12px;
  	border-radius: 12px;
  }

.result-summary {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 8px 10px;
	border-radius: 8px;
	background: #f0f7ff;
	border: 1px solid #dbeafe;
}

.summary-tag {
	flex-shrink: 0;
}

.summary-text {
	font-size: 13px;
	color: #1e3a8a;
	line-height: 1.6;
}

.sandbox-preview {
	margin-top: 10px;
	background: #f0f9ff;
	border: 1px solid #d9ecff;
}

  .answer-card {
  	padding: 14px 16px;
  	border-radius: 16px;
  	border: 1px solid rgba(72, 88, 117, 0.08);
  	background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
  	box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
  }

.answer-card :deep(.markdown-body) {
	font-size: 14px;
	line-height: 1.8;
	color: #1f2937;
}

.answer-card :deep(.markdown-body p:first-child) {
	margin-top: 0;
}

.answer-card :deep(.markdown-body p:last-child) {
	margin-bottom: 0;
}

  .code-block {
  	font-family: Consolas, monospace;
  	font-size: 12px;
  	color: #c7254e;
  	background-color: #f9f2f4;
  	padding: 10px;
  	border-radius: 10px;
  	overflow-x: auto;
  	margin: 0;
  }

.pagination-wrap {
	margin-top: 12px;
	display: flex;
	justify-content: flex-end;
}
</style>
