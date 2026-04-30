<script setup>
import {Calendar, User, Lock, Shop} from "@element-plus/icons-vue";
import {ElMessage} from "element-plus";

import {computed, ref} from "vue";
import {useRouter} from "vue-router";
import {userLogin1} from "@/api/user";
import {merchantLogin1} from "@/api/merchant";
import {adminLogin1} from "@/api/admin";

const router = useRouter()
const activeLoginTab = ref('user')
const loginThemeClass = computed(() => `login-container--${activeLoginTab.value}`)
const userName = ref('')
const userPassword = ref('')
const userLogin = () => {
  const user = {
    userName: userName.value,
    password: userPassword.value
  }
  userLogin1(user).then(res => {
    if (!res.data) {
      ElMessage({
        message: res.message,
        type: 'warning',
      })
    } else {
      ElMessage({
        message: '登陆成功',
        type: 'success',
      })
      router.push({ path: '/user' })
    }
  })
}
const register = () => {
  router.push({ path: '/register/user' })
}
const merchantName = ref('')
const merchantPassword = ref('')
const merchantLogin = () => {
  const merchant = {
    merchantName: merchantName.value,
    merchantPassword: merchantPassword.value
  }
  merchantLogin1(merchant).then(res => {
    if(!res.data){
      ElMessage({
        message: res.message,
        type: 'warning',
      })
    }else{
      ElMessage({
        message: '登陆成功',
        type: 'success',
      })
      router.push({path: '/merchant'})
    }
  })
}

const adminName = ref('')
const adminPassword = ref('')
const adminLogin = () => {
  const admin = {
    adminName: adminName.value,
    adminPassword: adminPassword.value
  }
  adminLogin1(admin).then(res => {
    if(!res.data){
      ElMessage({
        message: '管理员密码错误',
        type: 'warning',
      })
    }else{
      ElMessage({
        message: '登陆成功',
        type: 'success',
      })
      router.push({path: '/admin'})
    }
  })
}

const merchantRegister = () => {
  router.push({path: '/register/merchant'})
}
</script>

<template>
  <div class="login-container" :class="loginThemeClass">
    <div class="login-header">
      <div class="brand-mark">AI</div>
      <h1 class="app-title">智惠点评</h1>
      <p class="app-subtitle">面向生活服务的智能口碑分析与对话助手</p>
    </div>

    <div class="login-card">
      <el-tabs v-model="activeLoginTab" type="border-card" class="login-tabs" stretch>
        <el-tab-pane label="用户登录" name="user">
          <div class="form-container">
            <el-form ref="form">
              <el-form-item prop="userName">
                <el-input
                    v-model="userName"
                    clearable
                    placeholder="请输入用户名"
                    size="large"
                    :prefix-icon="User"
                ></el-input>
              </el-form-item>
              <el-form-item prop="userPassword">
                <el-input
                    v-model="userPassword"
                    clearable
                    placeholder="请输入密码"
                    show-password
                    size="large"
                    :prefix-icon="Lock"
                ></el-input>
              </el-form-item>
            </el-form>
            <div class="button-group">
              <el-button
                  type="primary"
                  @click="userLogin"
                  size="large"
                  round
                  class="login-btn"
              >登录</el-button>
              <el-button
                  @click="register"
                  size="large"
                  round
                  class="register-btn"
              >注册</el-button>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="商家登录" name="merchant">
          <div class="form-container">
            <el-form ref="form">
              <el-form-item prop="merchantName">
                <el-input
                    v-model="merchantName"
                    clearable
                    placeholder="请输入商家名称"
                    size="large"
                    :prefix-icon="Shop"
                ></el-input>
              </el-form-item>
              <el-form-item prop="merchantPassword">
                <el-input
                    v-model="merchantPassword"
                    clearable
                    placeholder="请输入密码"
                    show-password
                    size="large"
                    :prefix-icon="Lock"
                ></el-input>
              </el-form-item>
            </el-form>
            <div class="button-group">
              <el-button
                  type="primary"
                  @click="merchantLogin"
                  size="large"
                  round
                  class="login-btn"
              >登录</el-button>
              <el-button
                  @click="merchantRegister"
                  size="large"
                  round
                  class="register-btn"
              >注册</el-button>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="管理员登录" name="admin">
          <div class="form-container">
            <el-form ref="form">
              <el-form-item prop="adminName">
                <el-input
                    v-model="adminName"
                    clearable
                    placeholder="请输入管理员账号"
                    size="large"
                    :prefix-icon="User"
                ></el-input>
              </el-form-item>
              <el-form-item prop="adminPassword">
                <el-input
                    v-model="adminPassword"
                    clearable
                    placeholder="请输入密码"
                    show-password
                    size="large"
                    :prefix-icon="Lock"
                ></el-input>
              </el-form-item>
            </el-form>
            <div class="button-group">
              <el-button
                  type="primary"
                  @click="adminLogin"
                  size="large"
                  round
                  class="login-btn"
              >登录</el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.login-container {
  --login-primary: #3f6d61;
  --login-primary-dark: #173b3c;
  --login-primary-soft: rgba(63, 109, 97, 0.16);
  --login-secondary: #49677f;
  --login-accent-soft: rgba(59, 91, 124, 0.12);
  --login-border: rgba(190, 214, 205, 0.54);
  --login-text: #1f342e;
  --login-muted: #64756e;
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background:
      radial-gradient(circle at 18% 16%, var(--login-primary-soft), transparent 28%),
      radial-gradient(circle at 82% 18%, rgba(148, 176, 166, 0.18), transparent 26%),
      radial-gradient(circle at 50% 88%, var(--login-accent-soft), transparent 30%),
      linear-gradient(135deg, #f7f4ec 0%, #eef4ef 48%, #edf3f7 100%);
  padding: 28px 20px;
  box-sizing: border-box;
}

.login-container--user {
  --login-primary: #d97706;
  --login-primary-dark: #92400e;
  --login-primary-soft: rgba(217, 119, 6, 0.16);
  --login-secondary: #f2b56b;
  --login-accent-soft: rgba(47, 125, 107, 0.1);
  --login-border: rgba(232, 205, 178, 0.62);
  --login-text: #3a2716;
  --login-muted: #84664c;
}

.login-container--merchant {
  --login-primary: #2f7d6b;
  --login-primary-dark: #173b3c;
  --login-primary-soft: rgba(47, 125, 107, 0.16);
  --login-secondary: #82b7a3;
  --login-accent-soft: rgba(217, 168, 108, 0.12);
  --login-border: rgba(190, 214, 205, 0.62);
  --login-text: #1f342e;
  --login-muted: #64756e;
}

.login-container--admin {
  --login-primary: #3667ff;
  --login-primary-dark: #172335;
  --login-primary-soft: rgba(54, 103, 255, 0.14);
  --login-secondary: #6f8cff;
  --login-accent-soft: rgba(47, 125, 107, 0.1);
  --login-border: rgba(203, 213, 225, 0.68);
  --login-text: #182235;
  --login-muted: #64748b;
}

.login-container::before {
  content: "";
  position: absolute;
  inset: 32px;
  pointer-events: none;
  background-image:
      linear-gradient(var(--login-primary-soft) 1px, transparent 1px),
      linear-gradient(90deg, var(--login-primary-soft) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: radial-gradient(circle at center, black, transparent 72%);
}

.login-header {
  position: relative;
  z-index: 1;
  text-align: center;
  margin-bottom: 28px;
  color: var(--login-text);

  .brand-mark {
    width: 54px;
    height: 54px;
    margin: 0 auto 14px;
    border-radius: 18px;
    display: grid;
    place-items: center;
    color: #ffffff;
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 0.08em;
    background: linear-gradient(135deg, var(--login-primary-dark) 0%, var(--login-primary) 58%, var(--login-secondary) 100%);
    box-shadow: 0 18px 42px var(--login-primary-soft);
    transition: background 0.3s ease, box-shadow 0.3s ease;
  }

  .app-title {
    font-size: 42px;
    font-weight: 800;
    margin: 0 0 10px;
    letter-spacing: 0.08em;
    background: linear-gradient(120deg, var(--login-primary-dark) 0%, var(--login-primary) 58%, var(--login-secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .app-subtitle {
    font-size: 15px;
    color: var(--login-muted);
    margin: 0;
    letter-spacing: 0.04em;
  }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 480px;
  border-radius: 26px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 28px 80px rgba(31, 52, 46, 0.14);
  backdrop-filter: blur(18px);
}

.login-tabs {
  :deep(.el-tabs--border-card) {
    border: none;
    background: transparent;
    box-shadow: none;
  }

  :deep(.el-tabs__header) {
    background: rgba(247, 251, 248, 0.82);
    margin: 0;
    border-bottom: 1px solid var(--login-border);
  }

  :deep(.el-tabs__item) {
    font-size: 15px;
    font-weight: 700;
    padding: 0 20px;
    height: 56px;
    line-height: 56px;
    color: var(--login-muted);
    border: none;
    transition: color 0.2s ease, background-color 0.2s ease;
  }

  :deep(.el-tabs__item:hover) {
    color: var(--login-primary);
  }

  :deep(.el-tabs__item.is-active) {
    color: var(--login-primary-dark);
    background: rgba(255, 255, 255, 0.78);
  }

  :deep(.el-tabs__content) {
    padding: 34px;
    background: rgba(255, 255, 255, 0.78);
  }
}

.form-container {
  .el-form-item {
    margin-bottom: 25px;
  }

  .el-input {
    :deep(.el-input__wrapper) {
      min-height: 48px;
      border-radius: 16px;
      background: rgba(248, 251, 249, 0.9);
      box-shadow: 0 0 0 1px var(--login-border) inset;
      transition: box-shadow 0.2s ease, background-color 0.2s ease;
    }

    :deep(.el-input__wrapper.is-focus) {
      background: #ffffff;
      box-shadow: 0 0 0 1px var(--login-primary) inset;
    }

    :deep(.el-input__inner) {
      height: 48px;
      line-height: 48px;
      color: var(--login-text);
    }

    :deep(.el-input__prefix) {
      display: flex;
      align-items: center;
      padding-left: 10px;
      color: var(--login-muted);
    }
  }
}

.button-group {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;

  .el-button {
    flex: 1;
    height: 46px;
    font-weight: 700;
    letter-spacing: 0.08em;
    box-shadow: none !important;
  }

  .login-btn {
    background: linear-gradient(135deg, var(--login-primary-dark) 0%, var(--login-primary) 58%, var(--login-secondary) 100%);
    border: none;
    color: white;
    margin-right: 15px;

    &:hover {
      transform: translateY(-2px);
      filter: brightness(1.04);
    }
  }

  .register-btn {
    border-color: var(--login-border);
    color: var(--login-primary);
    background: rgba(232, 245, 239, 0.78);

    &:hover {
      border-color: var(--login-primary);
      color: #ffffff;
      background: var(--login-primary);
      transform: translateY(-2px);
    }
  }
}

@media (max-width: 768px) {
  .login-card {
    width: 94%;
  }

  .login-header {
    .app-title {
      font-size: 32px;
    }
  }

  .login-tabs {
    :deep(.el-tabs__content) {
      padding: 26px 22px;
    }
  }
}
</style>
