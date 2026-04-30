<script setup lang="ts">
// @ts-ignore
import {useRouter} from "vue-router";

declare global {
  interface Window {
    AMap: any;

  }
}

import { ref, onMounted, watch } from 'vue'
// @ts-ignore
import { merchantList, merchantSearchService } from '@/api/merchant'
// @ts-ignore
import { categorySearchService } from '@/api/category'

const userLocation = ref({ latitude: null, longitude: null })
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
  pageSize: 100000,
  merchantName: ''
})
const search = () => {
  merchantSearchService(searchForm.value).then(res => {
    merchants.value = res.data.records
    total.value = res.data.total
    renderMap()
  })
}
const list = () => {
  merchantList({ pageNum: searchForm.value.pageNum, pageSize: searchForm.value.pageSize }).then(res => {
    merchants.value = res.data.records
    total.value = res.data.total
    renderMap()
  })
}
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

function toRad(degrees) {
  return degrees * Math.PI / 180
}
function calcDistance(lat1, lng1, lat2, lng2) {
  if (lat1 < 25) {
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
function loadAMapScript() {
  return new Promise<void>((resolve, reject) => {
    if (window.AMap) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.type = 'text/javascript';

    script.src = 'https://webapi.amap.com/maps?v=2.0&key=8109e3d990408e66980ebe8eeea528ab&plugin=AMap.Geolocation,AMap.ControlBar,AMap.ToolBar,AMap.Scale,AMap.Driving';
    script.onload = () => resolve();
    script.onerror = reject;
    document.head.appendChild(script);
  });
}


const getUserLocation = () => {
  if (!window.AMap) {
    console.error('高德地图JS API未加载')
    return
  }
  const map = new window.AMap.Map(document.createElement('div'))
  map.plugin('AMap.Geolocation', function () {
    const geolocation = new window.AMap.Geolocation({
      enableHighAccuracy: true,
      timeout: 10000,
    })
    geolocation.getCurrentPosition(function (status, result) {
      if (status === 'complete') {
        let lat = result.position.lat
        let lng = result.position.lng
        if (lat < 26) {
          lat = 34.252379
          lng = 108.977936
        }
        userLocation.value.latitude = lat
        userLocation.value.longitude = lng
        renderMap()
      } else {
        console.error('定位失败', result)
      }
    })
  })
}
function centerMapToUser() {
  if (mapInstance && userLocation.value.latitude && userLocation.value.longitude) {
    mapInstance.setCenter([
      userLocation.value.longitude,
      userLocation.value.latitude
    ]);
    mapInstance.setZoom(14);
  }
}

const selectedMerchant = ref(null)
const driving = ref(null)

function speak(text: string) {
  const synth = window.speechSynthesis
  const utter = new SpeechSynthesisUtterance(text)
  utter.lang = 'zh-CN'
  utter.rate = 1
  synth.cancel()
  synth.speak(utter)
}
function planRoute(merchant) {
  if (!userLocation.value.latitude || !userLocation.value.longitude) {
    console.error('用户位置未知，无法路径规划')
    return
  }

  if (driving.value) {
    driving.value.clear()
  }

  driving.value = new window.AMap.Driving({
    map: mapInstance,
    panel: 'panel'
  })

  driving.value.search(
      new window.AMap.LngLat(userLocation.value.longitude, userLocation.value.latitude),
      new window.AMap.LngLat(merchant.longitude, merchant.latitude),
      (status, result) => {
        if (status === 'complete') {

          const route = result.routes[0]
          if (route) {
            const distanceKm = (route.distance / 1000).toFixed(2)
            const durationMin = Math.ceil(route.time / 60)

            speak(`已为您规划前往 ${merchant.merchantName} 的路线，预计耗时 ${durationMin} 分钟，全程 ${distanceKm} 公里。`)
          }
        } else {
          console.error('获取驾车数据失败：', result)
          speak('路径规划失败，请稍后重试')
        }
      }
  )
}

function clearRoute() {
  if (driving.value) {
    driving.value.clear();
    driving.value = null;
  }
  const panel = document.getElementById('panel');
  if (panel) {
    panel.innerHTML = '';
  }
}

let mapInstance = null

window._AMapSecurityConfig = {
  securityJsCode: "aea00ea10754323d95ce0bee4715a9a9",
};

function renderMap() {
  if (!window.AMap || !userLocation.value.latitude || !userLocation.value.longitude) return
  if (!mapInstance) {
    mapInstance = new window.AMap.Map('amap-container', {
      zoom: 11,
      center: [userLocation.value.longitude, userLocation.value.latitude]
    })
    mapInstance.plugin([
      'AMap.ControlBar',
      'AMap.ToolBar',
      'AMap.Scale',
      'AMap.MapType',
      'AMap.Driving'
    ], () => {
      mapInstance.addControl(new window.AMap.ControlBar({
        position: { right: '10px', top: '10px' }
      }));

      mapInstance.addControl(new window.AMap.ToolBar());
      mapInstance.addControl(new window.AMap.Scale());

      mapInstance.addControl(new window.AMap.MapType({
        defaultType: 0,
        showTraffic: false,
        showRoad: true,
        position: { right: '10px', top: '120px' }
      }));


    });
  } else {
    mapInstance.setCenter([userLocation.value.longitude, userLocation.value.latitude])
  }
  mapInstance.clearMap()

  merchants.value.forEach(m => {
    if (m.longitude && m.latitude) {
      const marker = new window.AMap.Marker({
        position: [m.longitude, m.latitude],
        map: mapInstance,
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png'
      })

      marker.setLabel({
        direction: 'top',
        offset: new window.AMap.Pixel(0, 0),
        content: `<div style="background-color:white;padding:2px 6px;border-radius:4px;border:1px solid #ccc;font-size:12px;color:#333;">${m.merchantName}</div>`
      })

      const dist = calcDistance(
          userLocation.value.latitude,
          userLocation.value.longitude,
          m.latitude,
          m.longitude
      )

      const infoContent = `
      <div style="font-size:13px; line-height:1.6;">
        <strong>${m.merchantName}</strong><br/>
        评分：${m.avgRating ?? '暂无'}<br/>
        距离：${dist.toFixed(2)} km
      </div>
    `

      const infoWindow = new window.AMap.InfoWindow({
        content: infoContent,
        offset: new window.AMap.Pixel(0, -30)
      })

      marker.on('mouseover', () => {
        infoWindow.open(mapInstance, marker.getPosition())
      })

      marker.on('mouseout', () => {
        infoWindow.close()
      })

      marker.on('click', () => {
        router.push(`/user/shop/${m.merchantId}`)
      })

      marker.on('rightclick', () => {
        planRoute(m);
      });
    }
  })
  new window.AMap.Marker({
    position: [userLocation.value.longitude, userLocation.value.latitude],
    map: mapInstance,
    icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
    title: '我的位置'
  })
}
watch(merchants, () => {
  renderMap()
})
const toList = ref(false)
const router = useRouter()
watch(toList, (val) => {
  if (val) {
    router.push('/user/search/list')
  }
})
onMounted( () => {
   loadAMapScript()
  getUserLocation()
  selectMainCategory('')

})

</script>

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
          v-model="toList"
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
    </div>
    </div>


  </div>

  <div class="map-shell">
  <div id="amap-container" @contextmenu.prevent>
   <el-button
     type="primary"
   @click="centerMapToUser"
    class="locate-button"
 >
    定位到我
 </el-button>
    <el-button
        v-if="driving"
        type="danger"
        @click="clearRoute"
        class="clear-route-button"
    >
      清除路线
    </el-button>
  </div>
  <div id="panel"></div>
  </div>
</template>

<style scoped>
.merchant-list-page {
  width: 100%;
  padding: 22px;
  margin-bottom: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(232, 205, 178, 0.7);
  box-shadow: 0 18px 44px rgba(196, 101, 34, 0.08);
  box-sizing: border-box;
}

.filter-panel {
  padding: 18px;
  border-radius: 20px;
  background: #fffaf4;
  border: 1px solid rgba(232, 205, 178, 0.78);
}

.category-row {
  margin-bottom: 14px;
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
}

.merchant-list-page :deep(.el-button-group .el-button) {
  margin-left: 0 !important;
  border-radius: 999px !important;
  border-left-color: var(--el-button-border-color);
}

.merchant-list-page :deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

.merchant-list-page :deep(.el-button--primary) {
  background: #d97706;
  border-color: #d97706;
}

.advanced-filter-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.2fr) repeat(4, minmax(150px, 1fr));
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
.filter-field :deep(.el-input-number) {
  width: 100%;
}

.merchant-list-page :deep(.el-input__wrapper),
.merchant-list-page :deep(.el-input-number) {
  border-radius: 14px;
  box-shadow: 0 0 0 1px rgba(232, 205, 178, 0.86) inset;
}

.filter-field :deep(.el-input-number) {
  overflow: hidden;
}

.filter-field :deep(.el-input-number .el-input__wrapper) {
  box-shadow: none;
}

.map-shell {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 16px;
  align-items: start;
}

  position: relative;
  width: 100%;
  height: 72vh;
  min-height: 560px;
  border-radius: 24px;
  overflow: hidden;
  border: 1px solid rgba(232, 205, 178, 0.78);
  box-shadow: 0 18px 44px rgba(196, 101, 34, 0.08);
}
.locate-button {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 999;
}
.clear-route-button {
  position: absolute;
  top: 16px;
  left: 112px;
  z-index: 999;
}

  height: 72vh;
  min-height: 560px;
  overflow: auto;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(232, 205, 178, 0.78);
  box-shadow: 0 18px 44px rgba(196, 101, 34, 0.08);
}

@media (max-width: 1100px) {
  .advanced-filter-row {
    grid-template-columns: repeat(2, minmax(180px, 1fr));
  }

  .map-shell {
    grid-template-columns: 1fr;
  }

    height: auto;
    min-height: 220px;
  }
}

@media (max-width: 640px) {
  .advanced-filter-row {
    grid-template-columns: 1fr;
  }
}
</style>
