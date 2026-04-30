<template>
  <div class="merchant-list-page">
    <div class="filter-panel">
      <div class="category-row category-toolbar">
      <el-button-group>
        <el-button :type="mainCategory === '' ? 'primary' : 'default'" @click="selectMainCategory('')">不限</el-button>
        <el-button :type="mainCategory === '餐饮' ? 'primary' : 'default'" @click="selectMainCategory('餐饮')">餐饮</el-button>
        <el-button :type="mainCategory === '娱乐' ? 'primary' : 'default'" @click="selectMainCategory('娱乐')">娱乐</el-button>
        <el-button :type="mainCategory === '购物' ? 'primary' : 'default'" @click="selectMainCategory('购物')">购物</el-button>
      </el-button-group>
      <el-switch
          v-model="toMap"
          class="mode-switch"
          width="100"
          inline-prompt
          style="--el-switch-on-color: #d97706; --el-switch-off-color: #2563eb"
          active-text="列表模式"
          inactive-text="地图模式"
      />
      </div>

    <div class="category-row" v-if="mainCategory">
      <el-button-group>
        <el-button :type="subCategory === '' ? 'primary' : 'default'" @click="selectSubCategory('')">不限</el-button>
        <template v-if="mainCategory === '餐饮'">
          <el-button :type="subCategory === '中餐' ? 'primary' : 'default'" @click="selectSubCategory('中餐')">中餐</el-button>
          <el-button :type="subCategory === '西餐' ? 'primary' : 'default'" @click="selectSubCategory('西餐')">西餐</el-button>
        </template>
        <template v-else-if="mainCategory === '娱乐'">
          <el-button :type="subCategory === '电影院' ? 'primary' : 'default'" @click="selectSubCategory('电影院')">电影院</el-button>
          <el-button :type="subCategory === 'KTV' ? 'primary' : 'default'" @click="selectSubCategory('KTV')">KTV</el-button>
        </template>
      </el-button-group>
    </div>

    <div class="category-row" v-if="(mainCategory === '餐饮' && (subCategory === '中餐' || subCategory === '西餐')) || (mainCategory === '娱乐' && (subCategory === '电影院' || subCategory === 'KTV'))">
      <el-button-group>
        <el-button :type="detailCategory === '' ? 'primary' : 'default'" @click="selectDetailCategory('')">不限</el-button>
        <template v-if="mainCategory === '餐饮' && subCategory === '中餐'">
          <el-button :type="detailCategory === '川菜' ? 'primary' : 'default'" @click="selectDetailCategory('川菜')">川菜</el-button>
          <el-button :type="detailCategory === '粤菜' ? 'primary' : 'default'" @click="selectDetailCategory('粤菜')">粤菜</el-button>
          <el-button :type="detailCategory === '鲁菜' ? 'primary' : 'default'" @click="selectDetailCategory('鲁菜')">鲁菜</el-button>
        </template>
        <template v-else-if="mainCategory === '餐饮' && subCategory === '西餐'">
          <el-button :type="detailCategory === '法式' ? 'primary' : 'default'" @click="selectDetailCategory('法式')">法式</el-button>
          <el-button :type="detailCategory === '意式' ? 'primary' : 'default'" @click="selectDetailCategory('意式')">意式</el-button>
          <el-button :type="detailCategory === '美式' ? 'primary' : 'default'" @click="selectDetailCategory('美式')">美式</el-button>
        </template>
        <template v-else-if="mainCategory === '娱乐' && subCategory === '电影院'">
          <el-button :type="detailCategory === 'IMAX厅' ? 'primary' : 'default'" @click="selectDetailCategory('IMAX厅')">IMAX厅</el-button>
          <el-button :type="detailCategory === '普通厅' ? 'primary' : 'default'" @click="selectDetailCategory('普通厅')">普通厅</el-button>
        </template>
        <template v-else-if="mainCategory === '娱乐' && subCategory === 'KTV'">
          <el-button :type="detailCategory === '大' ? 'primary' : 'default'" @click="selectDetailCategory('大')">大</el-button>
          <el-button :type="detailCategory === '中' ? 'primary' : 'default'" @click="selectDetailCategory('中')">中</el-button>
          <el-button :type="detailCategory === '小' ? 'primary' : 'default'" @click="selectDetailCategory('小')">小</el-button>
        </template>
      </el-button-group>
    </div>

      <div class="advanced-filter-row">
        <label class="filter-field">
          <span>商家名称</span>
          <el-input v-model="searchForm.merchantName" placeholder="商家名称" clearable @change="search()"/>
        </label>
        <label class="filter-field compact">
          <span>最低评分</span>
          <el-input-number v-model="searchForm.minScore" :precision="1" :step="1" :max="5" :min="0" @change="search()"/>
        </label>
        <label class="filter-field compact">
          <span>最高评分</span>
          <el-input-number v-model="searchForm.maxScore" :precision="1" :step="1" :max="5" :min="0" @change="search()"/>
        </label>
        <label class="filter-field compact">
          <span>最低价格</span>
          <el-input-number v-model="searchForm.minPrice" :precision="1" :step="10" :max="10000" :min="0" @change="search()"/>
        </label>
        <label class="filter-field compact">
          <span>最高价格</span>
          <el-input-number v-model="searchForm.maxPrice" :precision="1" :step="10" :max="10000" :min="0" @change="search()"/>
        </label>
        <label class="filter-field sort-field">
          <span>排序方式</span>
          <el-select v-model="searchForm.sortBy" placeholder="排序方式" @change="search()">
            <el-option
                v-for="item in options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
            />
          </el-select>
        </label>
      </div>
    </div>

    <el-card>
      <el-table :data="merchants" style="width: 100%">
        <el-table-column prop="merchantName" label="名称" width="110" />
        <el-table-column prop="description" label="描述" width="150" />
        <el-table-column prop="tag" label="标签" width="80" />
        <el-table-column prop="contactPhone" label="联系电话" width="120" />
        <el-table-column prop="contactEmail" label="联系邮箱" width="180" />
        <el-table-column prop="address" label="地址" width="180" />
        <el-table-column prop="avgRating" label="评分" width="80" />
        <el-table-column prop="priceLevel" label="人均消费" width="80" />
        <el-table-column prop="businessHours" label="营业时间" width="120" />
        <el-table-column
            prop="distance"
            label="距离 (km)"
            width="100"
            :formatter="(row) => row.distance != null ? row.distance.toFixed(2) + ' km' : '暂无数据'"
        />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="primary" size="small" @click="toMerchant(scope.row.merchantId)">访问</el-button>
            <el-button type="success" size="small" @click="collectMerchant(scope.row.merchantId)">收藏</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
          v-model:current-page="searchForm.pageNum"
          v-model:page-size="searchForm.pageSize"
          :page-sizes="[5, 10, 20, 50]"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="pageNoChange"
      />
    </el-card>
  </div>
  <div id="amap-container" style="display: none; width: 0; height: 0;"></div>

</template>

<script setup>
import {ref, onMounted, watch} from 'vue'
import {merchantList, merchantSearchService} from '@/api/merchant'
import { categorySearchService } from '@/api/category'
import { useRouter } from 'vue-router'
import {addFavorite, getCurrentUser, getFavoriteByUserAndMerchant} from "@/api/user";
import { ElMessage } from "element-plus";
import { useUserInfoStore } from '@/stores/userInfo';
import { ElMessageBox } from "element-plus";

const userInfoStore = useUserInfoStore();

const userLocation = ref({ latitude: '', longitude: '' })
const merchants = ref([])
const mainCategory = ref('')
const subCategory = ref('')
const detailCategory = ref('')
const total = ref(0)
const searchForm = ref({
  categoryId: '',
  minScore: 1,
  maxScore: 5,
  minPrice: 20,
  maxPrice: 40,
  sortBy: '',
  pageNum: 1,
  pageSize: 10,
  merchantName:''
})
const pageNoChange = (value) => {
  searchForm.pageNum = value
  search()
}
const handleSizeChange = (value) => {
  searchForm.pageSize = value
  search()
}

const search = () => {
  merchantSearchService(searchForm.value).then(res => {
    merchants.value = res.data.records
    total.value = res.data.total ;
    computeMerchantDistances()
    if (searchForm.value.sortBy === 'price') {
      merchants.value.sort((a, b) => {
        if (a.priceLevel == null) return 1;
        if (b.priceLevel == null) return -1;
        return a.priceLevel - b.priceLevel;
      })
    }
  })
}
const list = () => {
  merchantList({pageNum: searchForm.value.pageNum, pageSize: searchForm.value.pageSize}).then(res => {
    merchants.value = res.data.records
    total.value = res.data.total;
    computeMerchantDistances ()
  })
}
const options = [
  { value: 'distance', label: '距离' },
  { value: 'score', label: '评分' },
  { value: 'price', label: '价格' },
]
const selectMainCategory = (cat) => {
  mainCategory.value = cat
  subCategory.value = ''
  categorySearchService(cat).then(res => {
    searchForm.value.categoryId = res.data
    search()
  })
}

const selectSubCategory = (cat) => {
  subCategory.value = cat
  detailCategory.value = ''
  if (!cat) {
    if (mainCategory.value) {
      categorySearchService(mainCategory.value).then(res => {
        searchForm.value.categoryId = res.data
        search()
      })
    } else {
      list()
    }
  } else {
    categorySearchService(cat).then(res => {
      searchForm.value.categoryId = res.data
      search()
    })
  }
}
const selectDetailCategory = (cat) => {
  detailCategory.value = cat
  if (!cat) {
    if (subCategory.value) {
      categorySearchService(subCategory.value).then(res => {
        searchForm.value.categoryId = res.data
        search()
      })
    } else if (mainCategory.value) {
      categorySearchService(mainCategory.value).then(res => {
        searchForm.value.categoryId = res.data
        search()
      })
    } else {
      list()
    }
  } else {
    categorySearchService(cat).then(res => {
      searchForm.value.categoryId = res.data
      search()
    })
  }
}

const getUserLocation = () => {
  const script = document.createElement('script')
  script.src = 'https://webapi.amap.com/maps?v=2.0&key=8109e3d990408e66980ebe8eeea528ab&plugin=AMap.Geolocation'
  script.onload = () => {
    const map = new window.AMap.Map('amap-container')
    const geolocation = new window.AMap.Geolocation({
      enableHighAccuracy: true,
      timeout: 10000,
    })

    map.addControl(geolocation)
    geolocation.getCurrentPosition((status, result) => {
      if (status === 'complete' && result.position) {
        userLocation.value = {
          latitude: result.position.lat,
          longitude: result.position.lng,
        }
      } else {
        console.error('高德定位失败：', result.message)
        userLocation.value = { latitude: 39.9042, longitude: 116.4074 }
      }
    })
  }
  document.head.appendChild(script)
}
function toRad(degrees) {
  return degrees * Math.PI / 180
}

function calcDistance(lat1, lng1, lat2, lng2) {
  if (lat1 < 26) {
    lat1 = 34.252379;
    lng1 = 108.977936;
  }
  const R = 6371.0
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
      Math.sin(dLng / 2) * Math.sin(dLng / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}
const computeMerchantDistances = () => {
  if (!userLocation.value.latitude || !userLocation.value.longitude) return;

  merchants.value.forEach(merchant => {
    if (merchant.latitude && merchant.longitude) {
      merchant.distance = calcDistance(
          Number(userLocation.value.latitude),
          Number(userLocation.value.longitude),
          Number(merchant.latitude),
          Number(merchant.longitude)
      );
    } else {
      merchant.distance = null;
    }
  });
  if (searchForm.value.sortBy === 'distance') {
    merchants.value.sort((a, b) => {
      if (a.distance == null) return 1;
      if (b.distance == null) return -1;
      return a.distance - b.distance;
    });
  }
}
watch(
    () => userLocation.value,
    (newVal) => {
      if (newVal.latitude && newVal.longitude) {
        computeMerchantDistances()
      }
    },
    { deep: true }
)
const toMap = ref(true)
const router = useRouter()
watch(toMap, (val) => {
  if (!val) {
    router.push('/user/search/map')
  } else {
    router.push('/user/search/list')
  }
})
const toMerchant = (id) => {
  router.push(`/user/shop/${id}`)
}

const collectMerchant = (merchantId) => {
  if (!userInfoStore.userInfo || !userInfoStore.userInfo.userId) {
    ElMessage.error('用户信息未加载，请刷新页面后重试');
    return;
  }

  getFavoriteByUserAndMerchant(userInfoStore.userInfo.userId, merchantId)
    .then((response) => {
      const favorites = response.data.records;
      if (favorites.length > 0) {
        ElMessage.warning('该商家已收藏');
      } else {
        ElMessageBox.prompt('请输入收藏标签', '收藏商家', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputValue: '默认',
          inputPattern: /^[\u4e00-\u9fa5\w,]{1,8}$/,
          inputErrorMessage: '标签必须为1-8个字符且不能包含空格',
          inputPlaceholder: '请输入1-8个字符的标签'
        }).then(({ value }) => {
          addFavorite({ userId: userInfoStore.userInfo.userId, merchantId, tag: value })
            .then(() => {
              ElMessage.success('收藏成功');
            })
            .catch(() => {
              ElMessage.error('收藏失败，请稍后重试');
            });
        }).catch(() => {
          ElMessage.info('取消收藏');
        });
      }
    })
    .catch(() => {
      ElMessage.error('检查收藏状态失败，请稍后重试');
    });
};

onMounted(() => {
  getUserLocation()
  selectMainCategory('')
})

</script>

<style scoped>
.merchant-list-page {
  width: 100%;
  padding: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(232, 205, 178, 0.7);
  box-shadow: 0 18px 44px rgba(196, 101, 34, 0.08);
  box-sizing: border-box;
}

.category-row {
  margin-bottom: 14px;
}

.filter-panel {
  padding: 18px;
  margin-bottom: 18px;
  border-radius: 20px;
  background: #fffaf4;
  border: 1px solid rgba(232, 205, 178, 0.78);
}

.category-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.merchant-list-page :deep(.el-button-group) {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 8px;
  vertical-align: middle;
}

.merchant-list-page :deep(.el-button-group .el-button) {
  margin-left: 0 !important;
  border-radius: 999px !important;
  border-left-color: var(--el-button-border-color);
}

.mode-switch {
  flex: 0 0 auto;
}

.advanced-filter-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.2fr) repeat(4, minmax(150px, 1fr)) minmax(190px, 1fr);
  gap: 14px 16px;
  align-items: end;
  margin-top: 16px;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
  color: #9a5a12;
  font-size: 13px;
  font-weight: 700;
}

.filter-field :deep(.el-input),
.filter-field :deep(.el-input-number),
.filter-field :deep(.el-select) {
  width: 100%;
}

.filter-field :deep(.el-input-number) {
  overflow: hidden;
  border-radius: 14px;
}

.filter-field :deep(.el-input-number .el-input__wrapper) {
  box-shadow: none;
}

.filter-field :deep(.el-input-number__decrease),
.filter-field :deep(.el-input-number__increase) {
  border-color: rgba(232, 205, 178, 0.78);
}

.merchant-list-page :deep(.el-card) {
  margin-top: 18px;
  border: 1px solid rgba(232, 205, 178, 0.76);
  border-radius: 20px;
  box-shadow: none;
  overflow: hidden;
}

.merchant-list-page :deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

.merchant-list-page :deep(.el-button--primary) {
  background: #d97706;
  border-color: #d97706;
}

.merchant-list-page :deep(.el-input__wrapper),
.merchant-list-page :deep(.el-input-number),
.merchant-list-page :deep(.el-select__wrapper) {
  border-radius: 14px;
  box-shadow: 0 0 0 1px rgba(232, 205, 178, 0.86) inset;
}

.merchant-list-page :deep(.el-table th.el-table__cell) {
  background: #fff7ed;
  color: #9a5a12;
}

@media (max-width: 1100px) {
  .advanced-filter-row {
    grid-template-columns: repeat(2, minmax(180px, 1fr));
  }
}

@media (max-width: 640px) {
  .advanced-filter-row {
    grid-template-columns: 1fr;
  }
}
</style>
