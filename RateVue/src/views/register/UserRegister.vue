<script setup>
import { ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import {ElMessage} from 'element-plus'
import { useRouter } from 'vue-router'
import { userRegister } from "@/api/user"

const router = useRouter()

const form = ref({
  userName: '',
  phone: '',
  email: '',
  gender: 'O',
  password: '',
  birthday: '',
  avatar: '',
  showCollection: 'T',
  showComment: 'T'
})

const imageUrl = ref('')

const handleAvatarSuccess = (response,uploadFile) => {
  imageUrl.value = URL.createObjectURL(uploadFile.raw)
  form.value.avatar = response.data.url
}

const onSubmit = () => {
  const formattedForm = {
    ...form.value,
    birthday: typeof form.value.birthday === 'string'
        ? form.value.birthday.split('T')[0]
        : ''
  }

  userRegister(formattedForm).then(res => {
    if (res.data) {
      ElMessage({
        message: '注册成功',
        type: 'success'
      })
      router.push({ path: '/login' })
    } else {
      console.info(res.message)
      ElMessage({
        message: res.message,
        type: 'error'
      })
    }
  }).catch(error => {
    console.error('注册失败:', error)
    ElMessage({
      message: '注册失败: ' + error.message,
      type: 'error'
    })
  })
}
</script>

<template>
  <div class="regist-container">
    <h3>用户注册</h3>
    <el-form :model="form" label-width="auto" style="max-width: 600px">
      <el-form-item label="用户昵称" required>
        <el-input v-model="form.userName" placeholder="请输入昵称"/>
      </el-form-item>
      <el-form-item label="手机号">
        <el-input v-model="form.phone" placeholder="请输入手机号"/>
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="form.email" placeholder="请输入邮箱"/>
      </el-form-item>
      <el-form-item label="密码" required>
        <el-input v-model="form.password" placeholder="请输入密码" show-password/>
      </el-form-item>
      <el-form-item label="性别">
        <el-radio-group v-model="form.gender">
          <el-radio value="M">男</el-radio>
          <el-radio value="F">女</el-radio>
          <el-radio value="O">未知</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="头像">
        <el-upload
            class="avatar-uploader"
            :action="'/api/file/upload'"
            :show-file-list="false"
            :on-success="handleAvatarSuccess"
        >
          <img v-if="imageUrl" :src="imageUrl" class="avatar" />
          <el-icon v-else class="avatar-placeholder"><Plus /></el-icon>
        </el-upload>
      </el-form-item>
      <el-form-item label="生日">
        <el-date-picker
            v-model="form.birthday"
            type="date"
            placeholder="请选择生日"
            style="width: 100%"
            value-format="YYYY-MM-DD"
        />
      </el-form-item>
      <el-form-item label="设置">
        <el-checkbox v-model="form.showCollection" true-value="T" false-value="F">
          公开收藏
        </el-checkbox>
        <el-checkbox v-model="form.showComment" true-value="T" false-value="F">
          公开评论
        </el-checkbox>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSubmit">注册</el-button>
        <el-button @click="router.push('/login')">已有账号？去登录</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.regist-container {
  width: 600px;
  margin: 0 auto;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.avatar-uploader {
  width: 150px;
  height: 150px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
  position: relative;
}

.avatar {
  width: 100%;
  height: 100%;
  display: block;
}

.avatar-placeholder {
  font-size: 28px;
  color: #8c8c8c;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}
</style>
