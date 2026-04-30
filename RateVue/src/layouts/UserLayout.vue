<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search,
  Star,
  ChatDotRound,
  ChatLineRound,
  Tickets,
  User,
  SwitchButton
} from '@element-plus/icons-vue'
import {useUserInfoStore} from "@/stores/userInfo";
import {getCurrentUser} from "@/api/user";
import {ElMessage} from "element-plus";

const router = useRouter()
const defaultAvatar = ref('https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')

const goToProfile = () => {
  router.push('/user/profile')
}

const handleLogout = () => {
  userInfoStore.removeUserInfo();
  ElMessage.success("已成功退出登录");
  router.push('/login');
}

const userInfoStore = useUserInfoStore()
const getUserInfo = () => {
  getCurrentUser().then(res => {
    if (res.data) {
      userInfoStore.setUserInfo(res.data)
    } else {
      ElMessage.error("获取用户信息失败,请先登录")
      router.push({path:'/login'})
    }
  })
}
getUserInfo()

const avatarSrc = ref(userInfoStore.userInfo.avatar ? userInfoStore.userInfo.avatar : defaultAvatar.value)

watch(() => userInfoStore.userInfo.avatar, (val) => {
  avatarSrc.value = val ? val : defaultAvatar.value
})

function onAvatarError() {
  avatarSrc.value = defaultAvatar.value
}
</script>

<template>
  <div class="user-layout">
    <header class="user-header">
      <div class="header-container">
        <el-link underline="never" href="/user/search/list" class="logo">
          <h1 class="app-title">智惠点评</h1>
        </el-link>

        <nav class="main-nav">
          <router-link
              to="/user/search/list"
              class="nav-button"
              :class="{ active: $route.path.includes('/search') }"
          >
            <el-icon><Search /></el-icon>
            <span>商家搜索</span>
          </router-link>

          <router-link
              to="/user/collections"
              class="nav-button"
              :class="{ active: $route.path.includes('/collections') }"
          >
            <el-icon><Star /></el-icon>
            <span>收藏管理</span>
          </router-link>

          <router-link
              to="/user/comments"
              class="nav-button"
              :class="{ active: $route.path.includes('/comments') }"
          >
            <el-icon><ChatDotRound /></el-icon>
            <span>评价管理</span>
          </router-link>

          <router-link
              to="/user/assistant"
              class="nav-button"
              :class="{ active: $route.path.includes('/assistant') }"
          >
            <el-icon><ChatLineRound /></el-icon>
            <span>智能助手</span>
          </router-link>

          
        </nav>

        <div class="user-avatar" style="display: flex; align-items: center;">
          <el-dropdown trigger="click">
            <div class="avatar-wrapper">
              <el-avatar :size="40" :src="avatarSrc" @error="onAvatarError" />
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="goToProfile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <div style="margin-left: 12px; white-space: nowrap;"><h5>用户：{{ userInfoStore.userInfo.userName }}</h5></div>
        </div>
      </div>
    </header>

    <main class="user-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.user-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background:
    radial-gradient(circle at top right, rgba(255, 171, 87, 0.24), transparent 24%),
    linear-gradient(180deg, #fff9f3 0%, #fff0df 100%);
}

.user-header {
  position: sticky;
  top: 0;
  z-index: 1000;
  padding: 0;
  background: linear-gradient(180deg, rgba(196, 101, 34, 0.98), rgba(237, 140, 62, 0.98));
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 18px 40px rgba(196, 101, 34, 0.12);
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

.app-title {
  margin: 0;
  font-size: 23px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #fff8f2;
  background: none;
  -webkit-text-fill-color: initial;
}

.logo {
  flex-shrink: 0;
  text-decoration: none;
}

.logo h1 {
  margin: 0;
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
  color: rgba(255, 243, 233, 0.76);
  text-decoration: none;
  transition: transform 0.25s ease, background-color 0.25s ease, color 0.25s ease, box-shadow 0.25s ease;
  font-size: 13px;
  font-weight: 600;
  flex: 0 0 auto;
  white-space: nowrap;
  border: 1px solid transparent;
}

.nav-button:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

.nav-button.active {
  color: #fffaf5;
  background: rgba(255, 226, 194, 0.18);
  border-color: rgba(255, 233, 208, 0.24);
}

.nav-button :deep(.el-icon) {
  font-size: 18px;
}

.user-avatar {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #fff8f2;
}

.avatar-wrapper {
  display: flex;
  align-items: center;
}

.user-avatar :deep(.el-avatar) {
  border: 2px solid rgba(255, 255, 255, 0.18);
}

.user-avatar :deep(h5) {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #fff8f2;
}

.user-main {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 22px auto 0;
  padding: 0 20px;
  min-height: 0;
  box-sizing: border-box;
}
</style>
