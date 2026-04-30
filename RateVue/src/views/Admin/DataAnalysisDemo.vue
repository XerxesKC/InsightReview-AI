<script>
import * as echarts from 'echarts';
import { ref, onMounted } from 'vue';

export default {
  name: 'DataAnalysis',
  setup() {
    const fiveStarChart = ref(null);
    const commentCountChart = ref(null);
    const highRatingChart = ref(null);
    const ratingDistributionChart = ref(null);
    const userGrowthChart = ref(null);

    const mockData = {
      fiveStarMerchants: [
        { merchant_name: '川香居', five_star_count: 128 },
        { merchant_name: '星空KTV', five_star_count: 98 },
        { merchant_name: '粤菜馆', five_star_count: 87 },
        { merchant_name: '海底捞', five_star_count: 85 },
        { merchant_name: '星巴克', five_star_count: 76 },
        { merchant_name: '必胜客', five_star_count: 65 },
        { merchant_name: '麦当劳', five_star_count: 60 },
        { merchant_name: '肯德基', five_star_count: 58 },
        { merchant_name: '真功夫', five_star_count: 55 },
        { merchant_name: '兰州拉面', five_star_count: 50 },
        { merchant_name: '沙县小吃', five_star_count: 48 },
        { merchant_name: '黄焖鸡米饭', five_star_count: 45 },
        { merchant_name: '永和大王', five_star_count: 42 },
        { merchant_name: '呷哺呷哺', five_star_count: 40 },
        { merchant_name: '张亮麻辣烫', five_star_count: 38 },
        { merchant_name: '杨国福麻辣烫', five_star_count: 35 },
        { merchant_name: 'CoCo都可', five_star_count: 32 },
        { merchant_name: '蜜雪冰城', five_star_count: 30 },
        { merchant_name: '一点点', five_star_count: 28 },
        { merchant_name: '喜茶', five_star_count: 25 }
      ],
      commentCountMerchants: [
        { merchant_name: '川香居', comment_count: 256 },
        { merchant_name: '星空KTV', comment_count: 198 },
        { merchant_name: '海底捞', comment_count: 185 },
        { merchant_name: '星巴克', comment_count: 176 },
        { merchant_name: '麦当劳', comment_count: 165 },
        { merchant_name: '肯德基', comment_count: 158 },
        { merchant_name: '必胜客', comment_count: 155 },
        { merchant_name: '真功夫', comment_count: 145 },
        { merchant_name: '粤菜馆', comment_count: 140 },
        { merchant_name: '兰州拉面', comment_count: 135 },
        { merchant_name: '沙县小吃', comment_count: 130 },
        { merchant_name: '黄焖鸡米饭', comment_count: 125 },
        { merchant_name: '永和大王', comment_count: 120 },
        { merchant_name: '呷哺呷哺', comment_count: 115 },
        { merchant_name: '张亮麻辣烫', comment_count: 110 },
        { merchant_name: '杨国福麻辣烫', comment_count: 105 },
        { merchant_name: 'CoCo都可', comment_count: 100 },
        { merchant_name: '蜜雪冰城', comment_count: 95 },
        { merchant_name: '一点点', comment_count: 90 },
        { merchant_name: '喜茶', comment_count: 85 }
      ],
      highRatingMerchants: [
        { merchant_name: '川香居', avg_rating: 4.9 },
        { merchant_name: '粤菜馆', avg_rating: 4.8 },
        { merchant_name: '星空KTV', avg_rating: 4.7 },
        { merchant_name: '海底捞', avg_rating: 4.7 },
        { merchant_name: '星巴克', avg_rating: 4.6 },
        { merchant_name: '必胜客', avg_rating: 4.5 },
        { merchant_name: '真功夫', avg_rating: 4.5 },
        { merchant_name: '呷哺呷哺', avg_rating: 4.4 },
        { merchant_name: '永和大王', avg_rating: 4.4 },
        { merchant_name: '兰州拉面', avg_rating: 4.3 }
      ],
      ratingDistribution: [
        { rating_range: '4.5-5', count: 12 },
        { rating_range: '4-4.5', count: 25 },
        { rating_range: '3.5-4', count: 38 },
        { rating_range: '3-3.5', count: 20 },
        { rating_range: '2.5-3', count: 10 },
        { rating_range: '2-2.5', count: 5 },
        { rating_range: '1-2', count: 2 },
        { rating_range: '0-1', count: 1 }
      ],
      userGrowthData: [
        { year: '2020', new_users: 1200, total_users: 1200, active_percentage: 45.2 },
        { year: '2021', new_users: 2500, total_users: 3700, active_percentage: 52.3 },
        { year: '2022', new_users: 3800, total_users: 7500, active_percentage: 58.7 },
        { year: '2023', new_users: 4200, total_users: 11700, active_percentage: 62.1 },
        { year: '2024', new_users: 5000, total_users: 16700, active_percentage: 65.4 },
        { year: '2025', new_users: 3500, total_users: 20200, active_percentage: 68.2 }
      ]
    };

    const initCharts = () => {
      const fiveStarOption = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          name: '五星好评数量',
          nameLocation: 'middle',
          nameGap: 30,
          nameTextStyle: {
            fontWeight: 'bold',
            fontSize: 12
          }
        },
        yAxis: {
          type: 'category',
          data: mockData.fiveStarMerchants.map(item => item.merchant_name),
          axisLabel: {
            interval: 0,
            rotate: 30
          }
        },
        series: [{
          name: '五星好评',
          type: 'bar',
          data: mockData.fiveStarMerchants.map(item => item.five_star_count),
          itemStyle: {
            color: '#FFD700'
          }
        }]
      };

      const commentCountOption = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          name: '评论数量',
          nameLocation: 'middle',
          nameGap: 30,
          nameTextStyle: {
            fontWeight: 'bold',
            fontSize: 12
          }
        },
        yAxis: {
          type: 'category',
          data: mockData.commentCountMerchants.map(item => item.merchant_name),
          axisLabel: {
            interval: 0,
            rotate: 30
          }
        },
        series: [{
          name: '评论数',
          type: 'bar',
          data: mockData.commentCountMerchants.map(item => item.comment_count),
          itemStyle: {
            color: '#5470C6'
          }
        }]
      };

      const highRatingOption = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          name: '平均评分',
          max: 5,
          min: 0,
          nameLocation: 'middle',
          nameGap: 30,
          nameTextStyle: {
            fontWeight: 'bold',
            fontSize: 12
          }
        },
        yAxis: {
          type: 'category',
          data: mockData.highRatingMerchants.map(item => item.merchant_name),
          axisLabel: {
            interval: 0,
            rotate: 30
          }
        },
        series: [{
          name: '平均评分',
          type: 'bar',
          data: mockData.highRatingMerchants.map(item => item.avg_rating),
          itemStyle: {
            color: '#91CC75'
          }
        }]
      };

      const ratingDistributionOption = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center'
        },
        series: [
          {
            name: '评分分布',
            type: 'pie',
            radius: ['50%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '18',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: mockData.ratingDistribution.map(item => ({
              value: item.count,
              name: `${item.rating_range}星`
            }))
          }
        ]
      };

      const userGrowthOption = {
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
      };

      const fiveStarInstance = echarts.init(fiveStarChart.value);
      fiveStarInstance.setOption(fiveStarOption);

      const commentCountInstance = echarts.init(commentCountChart.value);
      commentCountInstance.setOption(commentCountOption);

      const highRatingInstance = echarts.init(highRatingChart.value);
      highRatingInstance.setOption(highRatingOption);

      const ratingDistributionInstance = echarts.init(ratingDistributionChart.value);
      ratingDistributionInstance.setOption(ratingDistributionOption);

      const userGrowthInstance = echarts.init(userGrowthChart.value);
      userGrowthInstance.setOption(userGrowthOption);

      window.addEventListener('resize', function() {
        fiveStarInstance.resize();
        commentCountInstance.resize();
        highRatingInstance.resize();
        ratingDistributionInstance.resize();
        userGrowthInstance.resize();
      });
    };

    onMounted(() => {
      initCharts();
    });

    return {
      fiveStarChart,
      commentCountChart,
      highRatingChart,
      ratingDistributionChart,
      userGrowthChart
    };
  }
};
</script>

<template>
  <div class="data-analysis-container">
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
      <div class="chart-container full-width">
        <h2>用户增长分析</h2>
        <div ref="userGrowthChart" class="chart"></div>
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
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  flex: 1;
  min-width: 0; 
}

.chart-container.full-width {
  flex: 0 0 100%;
}

.chart {
  width: 100%;
  height: 400px;
}

h2 {
  color: #666;
  margin-bottom: 15px;
  font-size: 18px;
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
