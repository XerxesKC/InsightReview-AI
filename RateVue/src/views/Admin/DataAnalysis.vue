<script>
import * as echarts from 'echarts';
import {ref, onMounted, nextTick, onUnmounted} from 'vue';
import { Loading } from '@element-plus/icons-vue';
import {
  getFiveStarMerchants,
  getMostCommentedMerchants,
  getHighestRatedMerchants,
  getRatingDistribution,
} from '@/api/admin';

export default {
  name: 'DataAnalysis',
  setup() {
    const fiveStarChart = ref(null);
    const commentCountChart = ref(null);
    const highRatingChart = ref(null);
    const ratingDistributionChart = ref(null);
    const userGrowthChart = ref(null);

    const loading = ref(true);
    const error = ref(false);
    const chartInstances = ref([]);
    const retryCount = ref(0);

    const mockData = {
      userGrowthData: [
        { year: '2020', new_users: 1200, total_users: 1200, active_percentage: 45.2 },
        { year: '2021', new_users: 2500, total_users: 3700, active_percentage: 52.3 },
        { year: '2022', new_users: 3800, total_users: 7500, active_percentage: 58.7 },
        { year: '2023', new_users: 4200, total_users: 11700, active_percentage: 62.1 },
        { year: '2024', new_users: 5000, total_users: 16700, active_percentage: 65.4 },
        { year: '2025', new_users: 3500, total_users: 20200, active_percentage: 68.2 }
      ]
    };

    const fetchAllData = async () => {
      try {
        const [fiveStar, commented, rated, distribution] = await Promise.all([
          getFiveStarMerchants(),
          getMostCommentedMerchants(),
          getHighestRatedMerchants(),
          getRatingDistribution()
        ]);


        return {
          fiveStarMerchants: (fiveStar.data || []).map(item => ({
            merchant_name: item.merchantName || '未知商户',
            five_star_count: item.five_star_count || 0
          })),

          commentCountMerchants: (commented.data || []).map(item => ({
            merchant_name: item.merchantName || '未知商户',
            comment_count: item.comment_count || 0
          })),

          highRatingMerchants: (rated.data || []).map(item => ({
            merchant_name: item.merchantName || '未知商户',
            avg_rating: Number(item.avgRating) || 0
          })),

          ratingDistribution: (distribution.data || []).map(item => ({
            rating_range: item.rating_range || '0-0',
            count: item.count || 0
          }))
        };
      } catch (err) {
        console.error('获取数据失败:', {
          error: err,
          response: err.response
        });
        throw err;
      }
    };

    const initChart = (chartRef, option) => {
      if (!chartRef.value) {
        console.error('图表容器不存在:', chartRef);
        return null;
      }


      try {
        const existingInstance = echarts.getInstanceByDom(chartRef.value);
        if (existingInstance) {
          existingInstance.dispose();
        }

        const instance = echarts.init(chartRef.value);
        instance.setOption(option);
        return instance;
      } catch (err) {
        console.error('初始化图表失败:', err);
        return null;
      }
    };

    const retry = () => {
      retryCount.value = 0;
      error.value = false;
      initCharts();
    };

    const initCharts = async () => {
      loading.value = true;
      error.value = false;

      try {
        const data = await fetchAllData();

        const checkContainer = (ref, name) => {
          if (!ref.value) {
            console.error(`容器${name}未找到:`, ref);
            return false;
          }
          return true;
        };

        if (!checkContainer(fiveStarChart, 'fiveStarChart') ||
            !checkContainer(commentCountChart, 'commentCountChart') ||
            !checkContainer(highRatingChart, 'highRatingChart') ||
            !checkContainer(ratingDistributionChart, 'ratingDistributionChart')) {
          throw new Error('图表容器未准备好');
        }

        chartInstances.value.forEach(instance => instance?.dispose());
        chartInstances.value = [];

        const fiveStarInstance = initChart(fiveStarChart, {

          tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
          grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
          xAxis: {
            type: 'value',
            name: '五星好评数量',
            nameLocation: 'middle',
            nameGap: 30,
            nameTextStyle: { fontWeight: 'bold', fontSize: 12 }
          },
          yAxis: {
            type: 'category',
            data: data.fiveStarMerchants.map(item => item.merchant_name),
            axisLabel: { interval: 0, rotate: 30 }
          },
          series: [{
            name: '五星好评',
            type: 'bar',
            data: data.fiveStarMerchants.map(item => item.five_star_count),
            itemStyle: { color: '#FFD700' }
          }]
        });

        const commentCountInstance = initChart(commentCountChart, {
          tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
          grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
          xAxis: {
            type: 'value',
            name: '评论数量',
            nameLocation: 'middle',
            nameGap: 30,
            nameTextStyle: { fontWeight: 'bold', fontSize: 12 }
          },
          yAxis: {
            type: 'category',
            data: data.commentCountMerchants.map(item => item.merchant_name),
            axisLabel: { interval: 0, rotate: 30 }
          },
          series: [{
            name: '评论数',
            type: 'bar',
            data: data.commentCountMerchants.map(item => item.comment_count),
            itemStyle: { color: '#5470C6' }
          }]
        });

        const highRatingInstance = initChart(highRatingChart, {
          tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
          grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
          xAxis: {
            type: 'value',
            name: '平均评分',
            max: 5,
            min: 0,
            nameLocation: 'middle',
            nameGap: 30,
            nameTextStyle: { fontWeight: 'bold', fontSize: 12 }
          },
          yAxis: {
            type: 'category',
            data: data.highRatingMerchants.map(item => item.merchant_name),
            axisLabel: { interval: 0, rotate: 30 }
          },
          series: [{
            name: '平均评分',
            type: 'bar',
            data: data.highRatingMerchants.map(item => item.avg_rating),
            itemStyle: { color: '#91CC75' }
          }]
        });

        const ratingDistributionInstance = initChart(ratingDistributionChart, {
          tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
          legend: { orient: 'vertical', right: 10, top: 'center' },
          series: [{
            name: '评分分布',
            type: 'pie',
            radius: ['50%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
            label: { show: false, position: 'center' },
            emphasis: {
              label: { show: true, fontSize: '18', fontWeight: 'bold'}
            },
            labelLine: { show: false },
            data: data.ratingDistribution.map(item => ({
              value: item.count,
              name: `${item.rating_range}星`
            }))
          }]
        });

        const userGrowthInstance = initChart(userGrowthChart, {
          tooltip: { trigger: 'axis', axisPointer: { type: 'cross', crossStyle: { color: '#999'}}},
          legend: { data: ['新增用户', '总用户数', '活跃用户比例']},
          xAxis: [
            {
              type: 'category',
              data: mockData.userGrowthData.map(item => item.year),
              axisPointer: { type: 'shadow'}
            }
          ],
          yAxis: [
            {
              type: 'value',
              name: '用户数量',
              min: 0,
              axisLabel: { formatter: '{value}'}
            },
            {
              type: 'value',
              name: '活跃比例',
              min: 0,
              max: 100,
              axisLabel: { formatter: '{value}%'}
            }
          ],
          series: [
            {
              name: '新增用户',
              type: 'bar',
              barGap: 0,
              data: mockData.userGrowthData.map(item => item.new_users)
            },
            {
              name: '总用户数',
              type: 'bar',
              data: mockData.userGrowthData.map(item => item.total_users)
            },
            {
              name: '活跃用户比例',
              type: 'line',
              yAxisIndex: 1,
              data: mockData.userGrowthData.map(item => item.active_percentage),
              itemStyle: { color: '#EE6666'}
            }
          ]
        });

        chartInstances.value = [
          fiveStarInstance,
          commentCountInstance,
          highRatingInstance,
          ratingDistributionInstance,
          userGrowthInstance
        ];

        const handleResize = () => {
          chartInstances.value.forEach(instance => {
            try {
              instance && instance.resize();
            } catch (e) {
              console.error('调整图表大小失败:', e);
            }
          });
        };

        window.addEventListener('resize', handleResize);

        onUnmounted(() => {
          window.removeEventListener('resize', handleResize);
          chartInstances.value.forEach(instance => {
            try {
              instance && instance.dispose();
            } catch (e) {
              console.error('销毁图表实例失败:', e);
            }
          });
        });

      } catch (err) {
        console.error('初始化失败:', err);

        if (retryCount.value < 3) {
          retryCount.value++;
          setTimeout(initCharts, 1000 * retryCount.value);
        } else {
          error.value = true;
        }
      } finally {
        loading.value = false;
      }
    };

    const checkAndInitCharts = () => {
      const containers = [
        fiveStarChart.value,
        commentCountChart.value,
        highRatingChart.value,
        ratingDistributionChart.value
      ];

      const allReady = containers.every(container =>
          container && container.offsetWidth > 0 && container.offsetHeight > 0
      );

      if (allReady) {
        initCharts();
      } else if (retryCount.value < 5) {
        retryCount.value++;
        setTimeout(checkAndInitCharts, 200);
      } else {
        console.error('容器准备超时，请检查DOM结构');
        error.value = true;
      }
    };


    onMounted(async () => {
      await nextTick();
      requestAnimationFrame(() => {
        window.dispatchEvent(new Event('resize'));
        setTimeout(() => {
          initCharts();
        }, 50);
      });
    });

    return {
      fiveStarChart,
      commentCountChart,
      highRatingChart,
      ratingDistributionChart,
      userGrowthChart,
      loading,
      error,
      retry,
      Loading,
      retryCount
    };
  }
};
</script>

<template>
  <div class="data-analysis-container">
    <div v-show="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div>数据加载中...<span v-if="retryCount > 0">(重试 {{ retryCount }}/5)</span></div>
    </div>

    <div v-show="error" class="error-message">
      <el-alert type="error" show-icon>
        数据加载失败，请<a @click="retry" style="cursor:pointer;margin-left:5px">点击重试</a>
      </el-alert>
    </div>

    <div v-show="!loading && !error" class="charts-wrapper">
      <div class="chart-row">
        <div class="chart-container">
          <h2>五星好评商户TOP20</h2>
          <div ref="fiveStarChart" class="chart"></div>
        </div>

        <div class="chart-container">
          <h2>评论数最多商户TOP20</h2>
          <div ref="commentCountChart" class="chart"></div>
        </div>
      </div>

      <div class="chart-row">
        <div class="chart-container">
          <h2>评分最高商户TOP10</h2>
          <div ref="highRatingChart" class="chart"></div>
        </div>

        <div class="chart-container">
          <h2>商户评分分布</h2>
          <div ref="ratingDistributionChart" class="chart"></div>
        </div>
      </div>

      <div class="chart-row">
        <div class="chart-container">
          <h2>用户增长分析</h2>
          <div ref="userGrowthChart" class="last-chart"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.data-analysis-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.chart-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 20px;
}

.chart-container {
  width: 100%;
  height: 450px;
  overflow: hidden; 
}

.chart {
  width: 600px;
  height: 400px;
}

.last-chart {
  width: 1300px;
  height: 400px;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 2s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  padding: 20px;
  background: #ffebee;
  color: #c62828;
  border-radius: 4px;
  margin: 20px;
  text-align: center;
}

.error-message button {
  margin-top: 10px;
  padding: 8px 16px;
  background: #c62828;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.error-message button:hover {
  background: #b71c1c;
}

h2 {
  color: #1e3a8a;
  margin: 0 0 15px;
  padding: 18px 20px 0;
  font-size: 18px;
  font-weight: 600;
}

.data-analysis-container {
  padding: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(203, 213, 225, 0.78);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
}

.chart-container {
  border-radius: 20px;
  border: 1px solid rgba(203, 213, 225, 0.72);
  background: #ffffff;
  box-shadow: none;
  overflow: hidden;
}

@media (max-width: 768px) {
  .chart-row {
    flex-direction: column;
  }

  .chart-container {
    margin-bottom: 20px;
  }

  .chart-container:last-child {
    margin-bottom: 0;
  }
}
</style>
