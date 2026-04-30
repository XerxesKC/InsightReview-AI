<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  User,
  Shop,
  DataAnalysis,
  SwitchButton, ChatDotRound, Setting, ArrowDown
} from '@element-plus/icons-vue'
import {getCurrentMerchant} from "@/api/merchant";
import {ElMessage} from "element-plus";
import {useMerchantInfoStore} from "@/stores/merchantInfo";
import {useAdminInfoStore} from "@/stores/adminInfo";
import {getCurrentAdmin} from "@/api/admin";

const router = useRouter()
const defaultAvatar = ref('https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')

const handleLogout = () => {
  router.push('/login')
}

const handleBusinessCommand = (path) => {
  router.push(path)
}

const adminInfoStore = useAdminInfoStore()
const getAdminInfo = () => {
  getCurrentAdmin().then(res => {

    if (res.data) {
      adminInfoStore.setAdminInfo(res.data)
    } else {
      ElMessage.error("获取管理员信息失败,请先登录")
    }
  })
}
getAdminInfo()
</script>

<template>
  <div class="admin-layout">
    <header class="admin-header">
      <div class="header-container">
        <el-link underline="never" href="/admin/users" class="logo">
          <h1>系统管理后台</h1>
        </el-link>

        <nav class="main-nav">
          <router-link
              to="/admin/users"
              class="nav-button"
              :class="{ active: $route.path.includes('/users') }"
          >
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </router-link>

          <router-link
              to="/admin/comment"
              class="nav-button"
              :class="{ active: $route.path.includes('/comment') }"
          >
            <el-icon><ChatDotRound /></el-icon>
            <span>评论管理</span>
          </router-link>

          <router-link
              to="/admin/merchants"
              class="nav-button"
              :class="{ active: $route.path.includes('/merchants') }"
          >
            <el-icon><Shop /></el-icon>
            <span>商家管理</span>
          </router-link>

          <router-link
              to="/admin/analytics"
              class="nav-button"
              :class="{ active: $route.path.includes('/analytics') }"
          >
            <el-icon><DataAnalysis /></el-icon>
            <span>数据分析</span>
          </router-link>

          <el-dropdown
              class="business-dropdown"
              trigger="click"
              @command="handleBusinessCommand"
          >
            <span
              class="nav-button business-trigger"
              :class="{ active: $route.path.includes('/doc-workbench') || $route.path.includes('/knowledge-base') || $route.path.includes('/system') || $route.path.includes('/documents') || $route.path.includes('/dialogue-log') || $route.path.includes('/pandas-analyzer') }"
            >
              <el-icon><Setting /></el-icon>
              <span>智能体业务</span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="/admin/documents">平台手册管理</el-dropdown-item>
                <el-dropdown-item command="/admin/doc-workbench">文档审核与加工</el-dropdown-item>
                <el-dropdown-item command="/admin/new-doc-workbench">智能文档处理</el-dropdown-item>
                <el-dropdown-item command="/admin/pandas-analyzer">Pandas分析器</el-dropdown-item>
                <el-dropdown-item command="/admin/knowledge-base">知识库管理</el-dropdown-item>
                <el-dropdown-item command="/admin/system">系统管理</el-dropdown-item>
                <el-dropdown-item command="/admin/dialogue-log">对话日志</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </nav>

        <div class="admin-controls">
          <el-dropdown trigger="click">
            <div class="admin-avatar">
              <el-avatar :size="36" :src="defaultAvatar" />
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <main class="admin-main">
      <router-view />
    </main>
  </div>
</template>


<style scoped>
.admin-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  color: var(--rv-text);
}

.admin-header {
  position: sticky;
  top: 0;
  z-index: 1000;
  padding: 0;
  background: linear-gradient(180deg, rgba(26, 40, 61, 0.98), rgba(23, 35, 53, 0.98));
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
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
  color: #f8fafc;
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
  color: rgba(237, 242, 247, 0.72);
  text-decoration: none;
  transition: transform 0.25s ease, background-color 0.25s ease, color 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
  font-size: 13px;
  font-weight: 600;
  flex: 0 0 auto;
  white-space: nowrap;
  border: 1px solid transparent;
}

.nav-button:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.08);
  transform: translateY(-1px) scale(1.01);
}

.nav-button.active {
  color: #ffffff;
  background: linear-gradient(135deg, rgba(54, 103, 255, 0.96), rgba(111, 140, 255, 0.94));
  border-color: rgba(255, 255, 255, 0.16);
  box-shadow: 0 16px 34px rgba(54, 103, 255, 0.3);
}

.nav-button .el-icon {
  font-size: 16px;
}

.business-trigger {
  cursor: pointer;
  user-select: none;
}

.arrow-icon {
  font-size: 12px;
  opacity: 0.7;
}

.admin-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-avatar {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.16);
  cursor: pointer;
  transition: transform 0.25s ease, background-color 0.25s ease;
}

.admin-avatar:hover {
  transform: translateY(-1px) scale(1.02);
  background: rgba(255, 255, 255, 0.16);
}

.admin-main {
  flex: 1;
  width: min(1480px, calc(100% - 40px));
  margin: 26px auto 44px;
}

:deep(.el-dropdown-menu) {
  padding: 12px;
  border-radius: 20px;
  border: 1px solid rgba(63, 79, 112, 0.1);
  box-shadow: 0 28px 60px rgba(24, 34, 56, 0.18);
}

:deep(.el-dropdown-menu__item) {
  min-width: 180px;
  border-radius: 14px;
  color: var(--rv-text);
  font-weight: 600;
  padding: 12px 14px;
}

:deep(.el-dropdown-menu__item:hover) {
  color: var(--rv-primary);
  background: rgba(49, 94, 251, 0.08);
}

@media (max-width: 960px) {
  .admin-header {
    padding: 0;
  }

  .header-container {
    flex-wrap: wrap;
    align-items: stretch;
    padding: 14px 12px;
  }

  .main-nav {
    order: 3;
    width: 100%;
  }

  .admin-main {
    width: min(100% - 24px, 1440px);
    margin-top: 18px;
  }
}
</style>
