<script setup lang="ts">
import {onMounted, reactive, ref} from 'vue'
import {Plus} from "@element-plus/icons-vue";
import {ElDrawer, ElMessage, ElMessageBox} from "element-plus";
import {merchantInsert, getContents1, removeContentById} from "@/api/merchantPost";
import {useMerchantInfoStore} from "@/stores/merchantInfo";
import {getCurrentMerchant} from "@/api/merchant";
import {useRouter} from "vue-router";
import {mergeAlias} from "vite";
import {getMerchantPostComments1} from "@/api/comment";
import {getUsers1} from "@/api/user";

const router = useRouter()
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
const content = reactive({
  merchantId: merchantInfoStore.merchantInfo.merchantId,
  title: '',
  content: '',
  imageUrl: '',
  videoUrl: '',
})

let imageUrl = ref('')
const handleImageSuccess = (response, uploadFile) => {
  imageUrl.value = URL.createObjectURL(uploadFile.raw)
  content.imageUrl = response.data.url
}
const videoUrl = ref('')
const handleVideoSuccess = (response, uploadFile) => {
  videoUrl.value = URL.createObjectURL(uploadFile.raw)
  content.videoUrl = response.data.url
}
const postContent = () => {
  if (content.title === '') {
    ElMessage.error('标题不能为空')
    return
  }
  if (content.content === '') {
    ElMessage.error('内容不能为空')
    return
  }
  merchantInsert(content).then(res => {
    if (res.data) {
      ElMessage.success('内容发布成功')
      getContents()
    } else {
      ElMessage.error('内容发布失败，请稍后再试')
    }
  }).catch(() => {
    ElMessage.error('内容发布失败，请稍后再试')
  })
  content.title = ''
  content.content = ''
  content.imageUrl = ''
  content.videoUrl = ''
  imageUrl.value = ''
  videoUrl.value = ''
  isShow.value = false
  router.push({ path: '/merchant/contents' })
}

const isShow = ref(false)
const showEditDialog = () => {
  isShow.value = true
}


const contents = ref([])
const getContents = () => {
  getContents1(merchantInfoStore.merchantInfo.merchantId).then(res => {
    contents.value = res.data
  })
}
const removeContent = (row) => {
  ElMessageBox.confirm(
      '是否确认删除当前动态？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
  )
      .then(() => {
        removeContentById(row).then((res)=>{
          if(res.data){
            ElMessage({
              message: '删除成功',
              type: 'success'
            })
          }
          getContents()
        })
      })
      .catch(() => {
      })
}

const drawerVisible = ref(false)
const currentContent = ref()
function showDetail(content) {
  currentContent.value = content
  drawerVisible.value = true
}
const merchantPostComments = ref([])
const getMerchantPostComments = () => {
  getMerchantPostComments1(merchantInfoStore.merchantInfo.merchantId).then(res => {
    merchantPostComments.value = res.data
  })
}
const users = ref([])
const getUsers = () =>{
  getUsers1().then(res => {
    users.value = res.data
  })
}
getMerchantPostComments()
getContents()
getUsers()
</script>

<template>
  <div>
    <div style="padding-bottom: 50px">
      <el-button type="primary" @click="showEditDialog" >发布新内容</el-button>
    </div>

    <div class="header">
      <el-table :data="contents" style="width: 100%" >
        <el-table-column prop="title" label="标题"  />
        <el-table-column prop="content" label="内容" />
        <el-table-column prop="image" label="图片" >
          <template #default="scope">
            <img height="100" :src="scope.row.imageUrl" alt="">
          </template>
        </el-table-column>
        <el-table-column prop="video" label="视频" >
          <template #default="scope">
            <video height="100" :src="scope.row.videoUrl" controls v-if="scope.row.videoUrl"></video>
            <span v-else></span>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button type="danger" size="small" @click="removeContent(scope.row)">删除</el-button>
            <el-button type="primary" size="small" @click="showDetail(scope.row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>


    <el-dialog
        v-model="isShow"
        title="修改信息"
        width="500"
    >
       <div class="content-manage">
    <el-input
        v-model="content.title"
        class="content-input"
        type="textarea"
        placeholder="起个标题吧"
        :rows="1"
    />
    <el-input
        v-model="content.content"
        class="content-input"
        type="textarea"
        placeholder="说点儿什么吧"
        :rows="5"
    />
    <el-form-item class="content-input">
      <el-form-item label="上传图片" class="content-text">
        <el-upload
            class="avatar-uploader"
            action="/api/file/upload"
            :show-file-list="false"
            :on-success="handleImageSuccess"
        >
        <img v-if="imageUrl" :src="imageUrl" class="avatar" style="height: 150px"/>
        <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
      </el-upload>
      </el-form-item>
    </el-form-item>
    <el-form-item class="content-input">
      <el-form-item label="上传视频" class="content-text">
        <el-upload
            class="avatar-uploader"
            action="/api/file/upload"
            :show-file-list="false"
            :on-success="handleVideoSuccess"
            accept="video/*"
        >
          <video v-if="videoUrl" :src="videoUrl" class="video-preview" controls style="height: 150px"/>
          <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
        </el-upload>
      </el-form-item>
    </el-form-item>
    <el-button type="primary" @click="postContent" >发布</el-button>
       </div>
    </el-dialog>

  <el-drawer
      v-model="drawerVisible"
      title="动态详情"
      direction="rtl"
      size="43%"
  >
    <div class="drawer-scroll-wrapper">
      <div class="el-drawer" style="padding-left:100px; padding-right:100px; width: 95%; height: 100%">
        <h1>{{ currentContent?.title }}</h1>
        <p>{{ currentContent?.content }}</p>
        <img height="200px" :src="currentContent?.imageUrl" alt="" />
        <video v-if="currentContent?.videoUrl" height="200" :src="currentContent.videoUrl" controls></video>
        <p style="font-size: 14px;"><img src="../../assets/islike.png" height="20px" width="20px"/>点赞量：{{ currentContent?.likeCount }}</p>
        <br>
        <h2>评论</h2>
        <div v-for="comment in merchantPostComments.filter(c => c.postId === currentContent?.postId)" :key="comment.id" class="comment-item">
          <img :src="users.find(user => user.userId === comment.userId)?.avatar" class="avatar" alt="" />
          <div class="info">
            <div class="username">{{ users.find(user => user.userId === comment.userId)?.userName }}</div>
            <div class="content">{{ comment.commentContent }}</div>
            <div>
              总评分：{{ comment.rating }} ⭐ |
              环境：{{ comment.envScore }} ⭐ |
              口味：{{ comment.tasteScore }} ⭐ |
              服务：{{ comment.serviceScore }} ⭐
            </div>
            <div class="time">{{ comment.updateTime }}</div>
          </div>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<style scoped>
.header{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: var(--el-color-white);
  border-bottom: 1px solid var(--el-border-color);
}
.content-manage {
  width: 500px;
  margin: 20px auto;
  height: 500px;
}
.content-input {
  width: 400px;
}

.content-upload {
  width: 800px;
  float: right;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.avatar-uploader .avatar {
  width: 114px;
  height: 114px;
  display: block;

}
.avatar-uploader .el-upload {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}

.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}

.el-icon.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 114px;
  height: 114px;
  text-align: center;
  float: left;
}
.comment-item {

  display: flex;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}
.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  margin-right: 16px;
}
.info {
  flex: 1;
}
.username {
  font-weight: bold;
  margin-bottom: 4px;
}
.content {
  color: #333;
  margin-bottom: 4px;
}
.time {
  color: #999;
  font-size: 12px;
}
.el-drawer {
  max-height: 80vh;
  overflow: auto;
}

.header {
  border-radius: 22px;
  border: 1px solid rgba(190, 214, 205, 0.78);
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 18px 44px rgba(22, 53, 45, 0.08);
  overflow: hidden;
}

.header :deep(.el-table th.el-table__cell) {
  background: #eef8f4;
  color: #226b5b;
}

:deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

:deep(.el-button--primary) {
  background: #2f7d6b;
  border-color: #2f7d6b;
}

.content-manage {
  border-radius: 18px;
}
</style>
