<template>
  <div style="width: 100%; height: 100%;">
    <div id="amap" style="width: 100%; height: 600px;"></div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { merchantSearchService } from '@/api/merchant'

const map = ref(null)
const markers = ref([])

const loadMerchants = async () => {
  const res = await merchantSearchService({
    pageNum: 1,
    pageSize: 100,
  })
  return res.data.data.records || []
}

const initMap = async () => {
  map.value = new window.AMap.Map('amap', {
    zoom: 12,
    center: [116.397428, 39.90923]
  })

  const merchants = await loadMerchants()
  merchants.forEach(m => {
    if (m.longitude && m.latitude) {
      const marker = new window.AMap.Marker({
        position: [m.longitude, m.latitude],
        title: m.merchantName
      })
      marker.setMap(map.value)
      marker.on('click', () => {
        new window.AMap.InfoWindow({
          content: `<b>${m.merchantName}</b><br/>评分：${m.avgRating || ''}<br/>地址：${m.address || ''}`
        }).open(map.value, marker.getPosition())
      })
      markers.value.push(marker)
    }
  })
}

onMounted(() => {
  if (window.AMap) {
    initMap()
  } else {
    const script = document.createElement('script')
    script.src = 'https://webapi.amap.com/maps?v=2.0&key=8109e3d990408e66980ebe8eeea528ab'
    script.onload = initMap
    document.head.appendChild(script)
  }
})
</script>

<style scoped>
  width: 100%;
  height: 600px;
}
</style>
