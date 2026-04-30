<template>
  <div class="dialogue-log-page">
    <el-card shadow="never" class="shell-card shell-card--filters">
      <template #header>
        <div class="shell-card__header">
          <div>
            <span class="shell-card__eyebrow">筛选条件</span>
            <h2 class="shell-card__title">对话日志筛选</h2>
          </div>
          <span class="shell-card__badge">多维检索</span>
        </div>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="用户 ID">
          <el-input v-model="searchForm.ownerId" placeholder="请输入用户 ID" size="small" />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="请输入问题或回答关键词" size="small" />
        </el-form-item>
        <el-form-item label="知识库">
          <el-input v-model="searchForm.kbName" placeholder="请输入知识库名称" size="small" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            size="small"
          />
        </el-form-item>
      </el-form>

      <div class="search-form__footer">
        <button class="action-pill action-pill--primary" type="button" @click="handleSearch">查询</button>
        <button class="action-pill" type="button" @click="resetForm">重置</button>
        <button class="action-pill action-pill--ghost" type="button" @click="exportDialogVisible = true">导出</button>
      </div>
    </el-card>

    <section class="metric-row">
      <article class="metric-card">
        <span class="metric-card__label">会话总数</span>
        <strong class="metric-card__value">{{ pagination.total }}</strong>
      </article>
      <article class="metric-card">
        <span class="metric-card__label">检索命中率</span>
        <strong class="metric-card__value">{{ Number(analysisData.retrieval_success_rate).toFixed(1) }}%</strong>
      </article>
      <article class="metric-card">
        <span class="metric-card__label">平均 Token 数</span>
        <strong class="metric-card__value">{{ Number(analysisData.average_response_time).toFixed(0) }}</strong>
      </article>
    </section>

    <el-card shadow="never" class="shell-card shell-card--table">
      <template #header>
        <div class="shell-card__header shell-card__header--wide">
          <div>
            <span class="shell-card__eyebrow">会话列表</span>
            <h2 class="shell-card__title">对话台账</h2>
            <p class="shell-card__hint">支持点击行查看完整对话、来源引用与会话详情。</p>
          </div>
          <span class="shell-card__badge">可追踪记录</span>
        </div>
      </template>

      <div class="table-stage">
        <el-table
          v-loading="loading"
          :data="sessionList"
          border
          stripe
          class="dialogue-table"
          @row-click="handleRowClick"
        >
          <el-table-column prop="session_id" label="会话 ID" width="220" />
          <el-table-column prop="owner_id" label="用户 ID" width="100" />
          <el-table-column prop="owner_type" label="用户类型" width="110" />
          <el-table-column prop="title" label="会话标题" min-width="220" />
          <el-table-column prop="turn_count" label="轮次" width="80" align="center" />
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button type="primary" link @click.stop="viewSessionDetail(scope.row.session_id)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10,20,50,100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handleCurrentChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <section class="analytics-grid">
      <el-card shadow="never" class="shell-card chart-card">
        <template #header>
          <div class="shell-card__header shell-card__header--wide">
            <div>
              <span class="shell-card__eyebrow">热门问题</span>
              <h2 class="shell-card__title">问题词云</h2>
            </div>
            <span class="chart-chip">语义聚合</span>
          </div>
        </template>
        <div id="wordCloudChart" class="chart-body"></div>
      </el-card>

      <el-card shadow="never" class="shell-card chart-card">
        <template #header>
          <div class="shell-card__header shell-card__header--wide">
            <div>
              <span class="shell-card__eyebrow">消息趋势</span>
              <h2 class="shell-card__title">每日消息量趋势</h2>
            </div>
            <span class="chart-chip">活跃变化</span>
          </div>
        </template>
        <div id="activityChart" class="chart-body"></div>
      </el-card>
    </section>

    <el-dialog v-model="dialogVisible" title="对话详情" width="900px" class="dialogue-modal">
      <template v-if="sessionDetail">
        <div class="session-info">
          <div><strong>会话 ID：</strong>{{ sessionDetail.session_id }}</div>
          <div><strong>用户 ID：</strong>{{ sessionDetail.owner_id }}</div>
          <div><strong>用户类型：</strong>{{ sessionDetail.owner_type }}</div>
          <div><strong>会话标题：</strong>{{ sessionDetail.title }}</div>
          <div><strong>创建时间：</strong>{{ formatDate(sessionDetail.created_at) }}</div>
        </div>

        <el-scrollbar max-height="480px">
          <div v-for="turn in sessionDetail.turns" :key="turn.turn_id" class="chat-turn">
            <div class="turn-header">
              <strong>第 {{ turn.turn_no }} 轮</strong>
              <span>{{ formatDate(turn.created_at) }}</span>
            </div>

            <div class="msg"><strong>用户：</strong>{{ turn.query }}</div>
            <div class="msg msg--answer"><strong>助手：</strong>{{ turn.answer }}</div>

            <div v-if="turn.rewritten_query" class="msg">
              <strong>改写问题：</strong>{{ turn.rewritten_query }}
            </div>

            <div v-if="turn._sources && turn._sources.length" class="sources">
              <div><strong>引用来源：</strong></div>
              <ul>
                <li v-for="(src, idx) in turn._sources" :key="idx">
                  {{ src.source || '未知来源' }}
                  <template v-if="src.score !== undefined">（得分：{{ Number(src.score).toFixed(4) }}）</template>
                </li>
              </ul>
            </div>
          </div>
        </el-scrollbar>
      </template>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="exportDialogVisible" title="导出对话日志" width="420px" class="dialogue-modal">
      <el-form :model="exportForm" label-width="90px">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportForm.format">
            <el-radio label="csv">CSV</el-radio>
            <el-radio label="excel">Excel</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exportDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleExport">导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { getDialogueLogs, getDialogueSessionDetail, exportDialogueLogs } from '@/api/dialogueLog'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import request from '@/utils/request'

export default {
  name: "DialogueLog",
  data() {
    return {
      analysisData: {
        hot_questions: [],
        retrieval_success_rate: 0,
        average_response_time: 0,
        user_activity: []
      },
      loading: false,
      searchForm: {
        ownerId: "",
        keyword: "",
        kbName: "",
        dateRange: []
      },
      sessionList: [],
      pagination: {
        current: 1,
        size: 10,
        total: 0
      },
      dialogVisible: false,
      exportDialogVisible: false,
      exportForm: {
        format: 'csv'
      },
      sessionDetail: null,
      wordCloudChart: null,
      activityChart: null,
      chartResizeObserver: null
    }
  },
  mounted() {
    this.fetchDialogueLogs()
    this.fetchAnalysisData()
    window.addEventListener('resize', this.resizeCharts)
    this.$nextTick(() => {
      if (typeof ResizeObserver !== 'undefined') {
        this.chartResizeObserver = new ResizeObserver(() => this.resizeCharts())
        const wordCloud = document.getElementById('wordCloudChart')
        const activity = document.getElementById('activityChart')
        if (wordCloud) this.chartResizeObserver.observe(wordCloud)
        if (activity) this.chartResizeObserver.observe(activity)
      }
    })
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeCharts)
    if (this.chartResizeObserver) this.chartResizeObserver.disconnect()
    if (this.wordCloudChart) this.wordCloudChart.dispose()
    if (this.activityChart) this.activityChart.dispose()
  },
  methods: {
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return dateStr;
      const pad = (n) => (n < 10 ? '0' + n : n);
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
    },
    async fetchAnalysisData() {
      try {
        const res = await request({ url: '/api/v1/dialogue-log/analysis', method: 'get' })
        this.analysisData = res.data
        this.$nextTick(() => this.initCharts())
      } catch (err) {
        console.error("获取分析数据失败", err)
      }
    },
    initCharts() {
      this.renderWordCloud()
      this.renderActivityChart()
    },
    renderWordCloud() {
      const target = document.getElementById('wordCloudChart')
      if (!target) return
      if (this.wordCloudChart) this.wordCloudChart.dispose()
      this.wordCloudChart = echarts.init(target)
      this.wordCloudChart.setOption({
        tooltip: { show: true },
        backgroundColor: 'transparent',
        borderWidth: 0,
        textStyle: { color: '#172132' },
        series: [{
          type: 'wordCloud',
          shape: 'circle',
          keepAspect: true,
          left: 'center',
          top: 'center',
          width: '96%',
          height: '96%',
          sizeRange: [14, 44],
          rotationRange: [-25, 70],
          gridSize: 8,
          drawOutOfBound: false,
          textStyle: {
            fontFamily: 'Segoe UI, PingFang SC, Microsoft YaHei, sans-serif',
            fontWeight: '700',
            color: () => {
              const colors = ['#315efb', '#4c6fd6', '#64748b', '#203152', '#7c8ca8'];
              return colors[Math.floor(Math.random() * colors.length)];
            }
          },
          data: this.analysisData.hot_questions
        }]
      })
      this.wordCloudChart.resize()
    },
    renderActivityChart() {
      const target = document.getElementById('activityChart')
      if (!target) return
      if (this.activityChart) this.activityChart.dispose()
      this.activityChart = echarts.init(target)
      this.activityChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '4%', right: '5%', bottom: '4%', containLabel: true },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          axisLine: { lineStyle: { color: 'rgba(100, 116, 139, 0.24)' } },
          axisLabel: { color: 'rgba(85, 99, 122, 0.78)' },
          splitLine: { show: false },
          data: this.analysisData.user_activity.map(i => i.date)
        },
        yAxis: {
          type: 'value',
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: 'rgba(85, 99, 122, 0.78)' },
          splitLine: { lineStyle: { color: 'rgba(100, 116, 139, 0.12)' } }
        },
        series: [{
          name: '消息量',
          type: 'line',
          smooth: true,
          showSymbol: false,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(79, 137, 255, 0.28)' },
              { offset: 1, color: 'rgba(79, 137, 255, 0.03)' }
            ])
          },
          lineStyle: { color: '#4f89ff', width: 3 },
          data: this.analysisData.user_activity.map(i => i.count)
        }]
      })
      this.activityChart.resize()
    },
    resizeCharts() {
      if (this.wordCloudChart) this.wordCloudChart.resize()
      if (this.activityChart) this.activityChart.resize()
    },
    parseSources(raw) {
      if(!raw) return []
      try { return JSON.parse(raw) } catch { return [] }
    },
    fetchDialogueLogs() {
      this.loading = true
      const params = {
        page: this.pagination.current,
        page_size: this.pagination.size,
        owner_id: this.searchForm.ownerId,
        keyword: this.searchForm.keyword,
        kb_name: this.searchForm.kbName
      }
      if(this.searchForm.dateRange.length === 2) {
        params.start_time = this.searchForm.dateRange[0]
        params.end_time = this.searchForm.dateRange[1]
      }
      getDialogueLogs(params).then(res => {
        const data = res.data || {}
        this.sessionList = data.items || []
        this.pagination.total = data.total || 0
        this.loading = false
      }).catch(() => {
        ElMessage.error("获取日志失败")
        this.loading = false
      })
    },
    handleSearch() {
      this.pagination.current = 1
      this.fetchDialogueLogs()
    },
    resetForm() {
      this.searchForm = { ownerId: "", keyword: "", kbName: "", dateRange: [] }
      this.fetchDialogueLogs()
    },
    handleCurrentChange(page) {
      this.pagination.current = page
      this.fetchDialogueLogs()
    },
    handleSizeChange(size) {
      this.pagination.size = size
      this.fetchDialogueLogs()
    },
    handleRowClick(row) {
      this.viewSessionDetail(row.session_id)
    },
    viewSessionDetail(sessionId) {
      getDialogueSessionDetail(sessionId).then(res => {
        const detail = res.data || {}
        const turns = (detail.turns || []).map(t => ({
          ...t,
          _sources: this.parseSources(t.sources)
        }))
        this.sessionDetail = { ...detail, turns }
        this.dialogVisible = true
      }).catch(() => {
        ElMessage.error("获取详情失败")
      })
    },
    handleExport() {
      const params = {
        format: this.exportForm.format,
        owner_id: this.searchForm.ownerId,
        keyword: this.searchForm.keyword,
        kb_name: this.searchForm.kbName
      }
      if(this.searchForm.dateRange && this.searchForm.dateRange.length === 2) {
        params.start_time = this.searchForm.dateRange[0]
        params.end_time = this.searchForm.dateRange[1]
      }
      exportDialogueLogs(params).then(res => {
        const rawData = res.data ? res.data : res;
        let blob;
        if (this.exportForm.format === 'csv') {
          blob = new Blob(['\ufeff', rawData], { type: 'text/csv;charset=utf-8' });
        } else {
          blob = new Blob([rawData], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        }
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dialogue_logs_${new Date().getTime()}.${this.exportForm.format === 'csv' ? 'csv' : 'xlsx'}`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        ElMessage.success("导出成功")
        this.exportDialogVisible = false
      }).catch((err) => {
        console.error(err)
        ElMessage.error("导出失败")
      })
    }
  }
}
</script>

<style scoped>
.dialogue-log-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.shell-card {
  border-radius: 28px;
  overflow: hidden;
}

.shell-card :deep(.el-card__body) {
  padding: 24px;
}

.shell-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.shell-card__header--wide {
  align-items: flex-start;
}

.shell-card__eyebrow {
  display: inline-flex;
  color: var(--rv-text-faint);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.shell-card__title {
  margin: 8px 0 0;
  color: var(--rv-text);
  font-size: 28px;
  line-height: 1.08;
}

.shell-card__hint {
  margin: 10px 0 0;
  color: var(--rv-text-soft);
  line-height: 1.7;
}

.shell-card__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(49, 94, 251, 0.08);
  color: var(--rv-primary);
  font-size: 12px;
  font-weight: 700;
}

.shell-card--filters,
.shell-card--table,
.chart-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 253, 0.97));
}

.search-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 18px;
}

.search-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

.search-form__footer {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}

.action-pill {
  appearance: none;
  border: 1px solid rgba(76, 93, 128, 0.12);
  background: rgba(255, 255, 255, 0.92);
  color: var(--rv-text);
  border-radius: 999px;
  padding: 12px 18px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease, background-color 0.22s ease;
}

.action-pill:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(20, 30, 45, 0.08);
}

.action-pill--primary {
  border-color: transparent;
  background: linear-gradient(135deg, #3667ff 0%, #5f86ff 100%);
  color: #ffffff;
  box-shadow: 0 16px 28px rgba(54, 103, 255, 0.2);
}

.action-pill--ghost {
  background: rgba(49, 94, 251, 0.08);
  color: var(--rv-primary);
  border-color: rgba(49, 94, 251, 0.08);
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.metric-card {
  padding: 24px 24px 22px;
  border: 1px solid rgba(70, 85, 116, 0.08);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 253, 0.97));
  box-shadow: 0 12px 26px rgba(18, 28, 45, 0.05);
}

.metric-card__label {
  display: block;
  color: var(--rv-text-soft);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.metric-card__value {
  display: block;
  margin-top: 14px;
  font-size: 34px;
  line-height: 1;
  color: var(--rv-text);
}

.table-stage {
  padding: 14px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(247, 249, 252, 0.92), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(72, 88, 117, 0.08);
}

.dialogue-table :deep(.el-table__body tr) {
  cursor: pointer;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 22px;
}

.analytics-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.analytics-grid > * {
  min-width: 0;
}

.chart-card {
  min-width: 0;
}

.chart-card :deep(.el-card__header),
.chart-card :deep(.el-card__body) {
  min-width: 0;
}

.chart-chip {
  display: inline-flex;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(49, 94, 251, 0.08);
  color: var(--rv-primary);
  font-size: 12px;
  font-weight: 700;
}

.chart-body {
  width: 100%;
  min-width: 0;
  height: 360px;
  overflow: hidden;
}

.session-info {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 18px;
  padding: 18px;
  margin-bottom: 18px;
  border-radius: 22px;
  background: rgba(247, 249, 252, 0.92);
}

.chat-turn {
  margin-bottom: 14px;
  padding: 16px;
  border-radius: 20px;
  border: 1px solid rgba(72, 88, 117, 0.1);
  background: rgba(255, 255, 255, 0.92);
}

.turn-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  color: var(--rv-text-soft);
}

.msg {
  margin-top: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(244, 246, 250, 0.92);
  line-height: 1.7;
}

.msg--answer {
  background: rgba(54, 103, 255, 0.06);
}

.sources {
  margin-top: 10px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(49, 94, 251, 0.06);
}

.sources ul {
  margin: 8px 0 0;
  padding-left: 18px;
}

@media (max-width: 1280px) {
  .analytics-grid,
  .metric-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .search-form,
  .session-info {
    grid-template-columns: 1fr;
  }
}
</style>
