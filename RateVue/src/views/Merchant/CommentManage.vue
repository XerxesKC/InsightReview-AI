<script setup lang="ts">
import {ref,computed} from 'vue'
import {ElDrawer, ElMessage} from 'element-plus'
import {useRouter} from "vue-router";
import {useMerchantInfoStore} from "@/stores/merchantInfo";
import {getCurrentMerchant} from "@/api/merchant";
import {getMerchantPostComments1, getMerchantComments1} from "@/api/comment";
import {getUsers1} from "@/api/user";
import {getContents1} from "@/api/merchantPost";

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

const merchantPostComments = ref([])
const merchantComments = ref([])
const users = ref([])
const drawerVisible = ref(false)
const currentComment = ref<any>(null)

function showDetail(comment: any) {
  currentComment.value = comment
  drawerVisible.value = true
}

const currentContent = computed(() => {
  if (!currentComment.value) return null
  return contents.value.find(content => content.postId === currentComment.value.postId)
})

const getMerchantPostComments = () => {
  getMerchantPostComments1(merchantInfoStore.merchantInfo.merchantId).then(res => {
    merchantPostComments.value = res.data
  })
}

const getMerchantComments = () => {
  getMerchantComments1(merchantInfoStore.merchantInfo.merchantId).then(res => {
    merchantComments.value = res.data
  })
}

const getUsers = () =>{
  getUsers1().then(res => {
    users.value = res.data
  })
}

const contents = ref([])
const getContents = () => {
  getContents1(merchantInfoStore.merchantInfo.merchantId).then(res => {
    contents.value = res.data
  })
}


getMerchantComments()
getMerchantPostComments()
getUsers()
getContents()
</script>

<template>
  <div class="comment-merchantpost-list">
    <h2>动态评论</h2>
    <div v-for="comment in merchantPostComments" :key="comment.commentId" class="comment-item">
      <img :src="users.find(user => user.userId === comment.userId)?.avatar" class="avatar" />
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
      <el-button type="primary" size="small" @click="showDetail(comment)">查看详情</el-button>
    </div>
  </div>

  <div class="comment-merchant-list">
    <h2>商家评论</h2>
    <div v-for="comment in merchantComments" :key="comment.id" class="comment-item">
      <img :src="users.find(user => user.userId === comment.userId)?.avatar" class="avatar"  alt=""/>
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

  <el-drawer
      v-model="drawerVisible"
      title="动态详情"
      direction="rtl"
      size="43%"
  >

    <div class="el-drawer" style="padding-left:100px; padding-right:100px; width: 95%; height: 100%">
      <div v-if="currentComment">
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
.comment-merchantpost-list {
  float: left;
  width: 45%;
  padding: 24px;
}
.comment-merchant-list {
  width: 45%;
  float: left;
  padding: 24px;
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

.comment-merchantpost-list,
.comment-merchant-list {
  margin-bottom: 18px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(190, 214, 205, 0.78);
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 18px 44px rgba(22, 53, 45, 0.08);
}

:deep(.el-table) {
  border-radius: 18px;
  overflow: hidden;
}

:deep(.el-table th.el-table__cell) {
  background: #eef8f4;
  color: #226b5b;
}

:deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

:deep(.el-button--primary),
:deep(.el-button--success) {
  background: #2f7d6b;
  border-color: #2f7d6b;
}
</style>
