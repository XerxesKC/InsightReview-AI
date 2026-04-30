<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserInfoStore } from '@/stores/userInfo'
import { getCurrentUser, updateCurrentUser } from '@/api/user'

const router = useRouter()
const userInfoStore = useUserInfoStore()

const userInfo = ref({
  userId: '',
  userName: '',
  password: '',
  phone: '',
  email: '',
  gender: '',
  birthday: '',
  avatar: '',
  showCollection: '',
  showComment: '',
  createTime: ''
})

const imageUrl = ref('')
const isEditing = ref(false)
const loading = ref(false)

const fetchUserInfo = async () => {
  try {
    loading.value = true
    const res = await getCurrentUser()
    if (res.data) {
      Object.assign(userInfo.value, {
        userId: res.data.userId,
        userName: res.data.userName,
        password: res.data.password,
        phone: res.data.phone,
        email: res.data.email,
        gender: res.data.gender,
        birthday: res.data.birthday,
        avatar: res.data.avatar,
        showCollection: res.data.showCollection,
        showComment: res.data.showComment,
        createTime: res.data.createTime
      })
      imageUrl.value = res.data.avatar || ''
      userInfoStore.setUserInfo(res.data)
    }
  } catch (error) {
    ElMessage.error('获取用户信息失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const handleAvatarSuccess = (response, uploadFile) => {
  imageUrl.value = URL.createObjectURL(uploadFile.raw)
  userInfo.value.avatar = response.data.url
}

const onSubmit = async () => {
  try {
    loading.value = true
    const formattedData = {
      ...userInfo.value,
      birthday: typeof userInfo.value.birthday === 'string'
          ? userInfo.value.birthday.split('T')[0]
          : userInfo.value.birthday
    }

    const res = await updateCurrentUser(formattedData)
    if (res.data) {
      ElMessage.success('信息更新成功')
      isEditing.value = false
      Object.assign(userInfo.value, {
        userName: res.data.userName,
        password: res.data.password,
        phone: res.data.phone,
        email: res.data.email,
        gender: res.data.gender,
        birthday: res.data.birthday,
        avatar: res.data.avatar,
        showCollection: res.data.showCollection,
        showComment: res.data.showComment
      })
      imageUrl.value = res.data.avatar || ''
      userInfoStore.setUserInfo(res.data)

    } else {
      ElMessage.error('更新失败: ' + res.message)
      await fetchUserInfo()
    }
  } catch (error) {
    ElMessage.error('更新失败: ' + error.message)
    await fetchUserInfo()
  } finally {
    loading.value = false
  }
}

fetchUserInfo()

</script>

<template>
  <div class="profile-container">
    <h3>个人中心</h3>

    <el-card v-loading="loading">
      <div class="profile-header">
        <el-upload
            v-if="isEditing"
            class="avatar-uploader"
            :action="'/api/file/upload'"
            :show-file-list="false"
            :on-success="handleAvatarSuccess"
        >
          <img v-if="imageUrl" :src="imageUrl" class="avatar" />
          <el-icon v-else class="avatar-placeholder">
            <i class="el-icon-user-solid"></i>
          </el-icon>
        </el-upload>
        <div v-else class="avatar-display">
          <img v-if="imageUrl" :src="imageUrl" class="avatar" />
          <el-icon v-else class="avatar-placeholder">
            <i class="el-icon-user-solid"></i>
          </el-icon>
        </div>

        <div class="profile-basic">
          <h2>{{ userInfoStore.userInfo.userName }}</h2>
          <p>注册时间: {{ userInfo.createTime ? new Date(userInfo.createTime).toLocaleDateString() : '暂无数据' }}</p>
        </div>
      </div>

      <el-form
          :model="userInfo"
          label-width="100px"
          style="max-width: 600px; margin-top: 20px; margin-left: auto; margin-right: auto;"
      >
        <el-form-item label="用户昵称">
          <el-input v-model="userInfo.userName" :disabled="!isEditing" />
        </el-form-item>

        <el-form-item label="密码">
          <el-input v-model="userInfo.password" type="password" show-password :disabled="!isEditing" />
        </el-form-item>

        <el-form-item label="手机号">
          <el-input v-model="userInfo.phone" :disabled="!isEditing" />
        </el-form-item>

        <el-form-item label="邮箱">
          <el-input v-model="userInfo.email" :disabled="!isEditing" />
        </el-form-item>

        <el-form-item label="性别">
          <el-radio-group v-model="userInfo.gender" :disabled="!isEditing">
            <el-radio value="M">男</el-radio>
            <el-radio value="F">女</el-radio>
            <el-radio value="O">未知</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="生日">
          <el-date-picker
              v-model="userInfo.birthday"
              type="date"
              placeholder="选择生日"
              style="width: 100%"
              :disabled="!isEditing"
              value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="隐私设置">
          <el-checkbox
              v-model="userInfo.showCollection"
              true-value="T"
              false-value="F"
              :disabled="!isEditing"
          >
            公开收藏
          </el-checkbox>
          <el-checkbox
              v-model="userInfo.showComment"
              true-value="T"
              false-value="F"
              :disabled="!isEditing"
          >
            公开评论
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <template v-if="!isEditing">
            <el-button type="primary" @click="isEditing = true">编辑资料</el-button>
            <el-button @click="router.push('/user/search/list')">返回首页</el-button>
          </template>
          <template v-else>
            <el-button type="primary" @click="onSubmit" :loading="loading">保存修改</el-button>
            <el-button @click="isEditing = false; fetchUserInfo()">取消</el-button>
          </template>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.profile-container {
  width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.profile-header {
  display: flex;
  align-items: center;
  margin-left: 80px;
  margin-top: 30px;
  margin-bottom: 30px;
}

.avatar-uploader, .avatar-display {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid #eee;
  margin-right: 20px;
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 60px;
  color: #8c8c8c;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.profile-basic h2 {
  margin: 0;
  font-size: 24px;
}

.profile-basic p {
  margin: 5px 0 0;
  color: #999;
  font-size: 14px;
}

</style>

