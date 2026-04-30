<script setup>
import { useRouter } from 'vue-router'
import {
  Shop,
  DataBoard,
  ChatLineRound,
  TrendCharts,
  SwitchButton, Files, ChatRound
} from '@element-plus/icons-vue'
import {useMerchantInfoStore} from "@/stores/merchantInfo";
import {getCurrentMerchant} from "@/api/merchant";
import {ElMessage} from "element-plus";

const router = useRouter()

const handleLogout = () => {
  merchantInfoStore.removeMerchantInfo();
  router.push('/login')
}

const merchantInfoStore = useMerchantInfoStore()
const getMerchantInfo = () => {
  getCurrentMerchant().then(res => {
    if (res.data) {
      merchantInfoStore.setMerchantInfo(res.data)
    } else {
      ElMessage.error("获取商家信息失败,请先登录")
      router.push({path:'/login'})
    }
  })
}
getMerchantInfo()

const gotoMerchantProfile = () => {
  router.push('/merchant/profile')
}

const checkVerificationStatus = (path) => {
  const verificationStatus = merchantInfoStore.merchantInfo.verificationStatus

  if (path === '/merchant/profile') {
    return true
  }

  if (verificationStatus !== 2) {
    let message = ''
    if (verificationStatus === 0) {
      message = '您的商家认证未通过，无法访问此页面'
    } else if (verificationStatus === 1) {
      message = '您的商家认证正在审核中，请耐心等待'
    } else {
      message = '请先完成商家认证'
    }

    ElMessage.warning(message)
    return false
  }

  return true
}

const handleNavigation = (path) => {
  if (checkVerificationStatus(path)) {
    router.push(path)
  }
}

const getActivePath = (routePath) => {
  if (routePath.includes('/profile')) return '/merchant/profile'
  if (routePath.includes('/contents')) return '/merchant/contents'
  if (routePath.includes('/comments')) return '/merchant/comments'
  if (routePath.includes('/analytics')) return '/merchant/analytics'
  if (routePath.includes('/documents')) return '/merchant/documents'
  if (routePath.includes('/assistant')) return '/merchant/assistant'
  return ''
}
</script>

<template>
  <div class="merchant-layout">
    <header class="merchant-header">
      <div class="header-container">
        <el-link underline="never" href="/merchant/profile" class="logo">
          <h1>智惠点评</h1>
        </el-link>

        <nav class="main-nav">
          <div
              @click="handleNavigation('/merchant/profile')"
              class="nav-button"
              :class="{ active: $route.path.includes('/profile') }"
          >
            <el-icon><Shop /></el-icon>
            <span>店铺信息</span>
          </div>

          <div
              @click="handleNavigation('/merchant/contents')"
              class="nav-button"
              :class="{
                active: $route.path.includes('/contents'),
                disabled: merchantInfoStore.merchantInfo.verificationStatus !== 2
              }"
          >
            <el-icon><DataBoard /></el-icon>
            <span>动态管理</span>
          </div>

          <div
              @click="handleNavigation('/merchant/comments')"
              class="nav-button"
              :class="{
                active: $route.path.includes('/comments'),
                disabled: merchantInfoStore.merchantInfo.verificationStatus !== 2
              }"
          >
            <el-icon><ChatLineRound /></el-icon>
            <span>评论处理</span>
          </div>

          <div
              @click="handleNavigation('/merchant/documents')"
              class="nav-button"
              :class="{
                active: $route.path.includes('/documents'),
                disabled: merchantInfoStore.merchantInfo.verificationStatus !== 2
              }"
          >
            <el-icon><Files /></el-icon>
            <span>文档管理</span>
          </div>

          <div
              @click="handleNavigation('/merchant/merchantAssistant')"
              class="nav-button"
              :class="{
                active: $route.path.includes('/merchantAssistant'),
                disabled: merchantInfoStore.merchantInfo.verificationStatus !== 2
              }"
          >
            <el-icon><ChatRound /></el-icon>
            <span>智能助手</span>
          </div>


        </nav>

        <div class="logout-area">
          <div>
            <el-button @click="gotoMerchantProfile">{{ merchantInfoStore.merchantInfo.merchantName }}</el-button>
            <el-tooltip content="退出登录" placement="bottom">
              <el-button
                  circle
                  @click="handleLogout"
                  class="logout-button"
              >
                <el-icon><SwitchButton /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>
      </div>
    </header>

    <main class="merchant-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.merchant-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(96, 170, 145, 0.2), transparent 24%),
    linear-gradient(180deg, #f3faf7 0%, #e9f4ef 100%);
}

.merchant-header {
  position: sticky;
  top: 0;
  z-index: 1000;
  padding: 0;
  background: linear-gradient(180deg, rgba(30, 67, 58, 0.98), rgba(38, 86, 74, 0.98));
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 18px 40px rgba(22, 53, 45, 0.14);
}

.header-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  max-width: 1440px;
  margin: 0 auto;
  padding: 14px 8px;
  min-height: 76px;
}

.logo {
  flex-shrink: 0;
  text-decoration: none;
}

.logo h1 {
  margin: 0;
  font-size: 23px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #f7fdf9;
}

.main-nav {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: none;
}

.main-nav::-webkit-scrollbar {
  display: none;
}

.nav-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  border-radius: 999px;
  color: rgba(238, 247, 243, 0.74);
  text-decoration: none;
  transition: transform 0.25s ease, background-color 0.25s ease, color 0.25s ease, box-shadow 0.25s ease;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  flex: 0 0 auto;
  white-space: nowrap;
  border: 1px solid transparent;
}

.nav-button:hover:not(.disabled) {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

.nav-button.active:not(.disabled) {
  color: #f7fffb;
  background: rgba(124, 216, 184, 0.16);
  border-color: rgba(148, 228, 198, 0.24);
}

.nav-button.disabled {
  color: rgba(231, 239, 235, 0.32);
  cursor: not-allowed;
}

.nav-button .el-icon {
  font-size: 18px;
}

.logout-area > div {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logout-area :deep(.el-button:not(.logout-button)) {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.08);
  color: #f5fbf8;
  border-radius: 999px;
  padding: 10px 16px;
  box-shadow: none;
}

.logout-button {
  color: #f5fbf8;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: none;
}

.logout-button:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.14);
}

.merchant-main {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 22px auto 0;
  padding: 0 20px;
  min-height: 0;
  box-sizing: border-box;
}
</style>
