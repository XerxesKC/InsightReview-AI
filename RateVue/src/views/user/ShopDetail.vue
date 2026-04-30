<script setup >
import {ref, onMounted, computed} from 'vue'
import { useRoute } from 'vue-router'
import {addLikeCount, getContents1} from '@/api/merchantPost'
import { selectById } from "@/api/merchant"
import {searchComment, addReply, queryReplies, searchPostComment, getMerchantPostComments1} from "@/api/comment"
import {ElDrawer, ElMessage, ElMessageBox} from 'element-plus'
import {addComment,deleteComment} from "@/api/comment";
import { useUserInfoStore } from '@/stores/userInfo';
import {Plus} from "@element-plus/icons-vue";
import {getUsers1} from "@/api/user";
import {useMerchantInfoStore} from "@/stores/merchantInfo";
const route = useRoute()
const merchantId = route.params.id
const postId = ref(null)
const contents = ref([])
const merchant = ref({})
const comments = ref([])
const userInfoStore = useUserInfoStore();
const currentComment = ref('')
const drawerVisible = ref(false)
const merchantPostComments = ref([])
const commentRepliesMap = ref({})  // key 为 commentId，value 为数组 replies

const loadRepliesForComment = async (comment) => {
  const commentId = comment.commentId
  const replyTo = comment.userId

  try {
    const res = await queryReplies(commentId, replyTo)
    commentRepliesMap.value[commentId] = res.data || []
  } catch (error) {
    console.error('获取回复失败', error)
    commentRepliesMap.value[commentId] = []
  }
}

const dialogVisible = ref(false)
const commentForm = ref({
  commentContent: '',
  rating: 0,
  envScore: 0,
  tasteScore: 0,
  serviceScore: 0,
  image: '',
  video: ''
})
let imageUrl = ref('')
const handleImageSuccess = (response, uploadFile) => {
  imageUrl.value = URL.createObjectURL(uploadFile.raw)
  commentForm.image = response.data.url
}
const videoUrl = ref('')
const handleVideoSuccess = (response, uploadFile) => {
  videoUrl.value = URL.createObjectURL(uploadFile.raw)
  commentForm.video = response.data.url
}
const handleCommentSubmit = () => {
  if (!commentForm.value.commentContent.trim()) {
    ElMessage.warning('评论内容不能为空')
    return
  }

  const newComment = {
    ...commentForm.value,
    merchantId: merchantId,
    postId:postId.value,
    image: commentForm.image,
    video: commentForm.video,
    userId: userInfoStore.userInfo.userId || '',
  }

  addComment(newComment).then(res => {
    if (res.data) {
      ElMessage.success('评论成功（待审核）')
      dialogVisible.value = false
      getComments() // 刷新评论列表
    } else {
      ElMessage.error('评论失败，请稍后重试')
    }
  }).catch(() => {
    ElMessage.error('评论请求异常')
  })
}
const getContents = () => {
  getContents1(merchantId).then(res => contents.value = res.data)
}
const getUsers = () =>{
  getUsers1().then(res => {
    users.value = res.data
  })
}
const handleDrawerClose = () => {
  postId.value = ''
}
const users = ref([])
const getMerchantInfo = () => {
  selectById(merchantId).then(res => {
    if (res.data) merchant.value = res.data
  })
}
const getComments = () => {
  searchComment({ merchantId, page: 1, size: 10 }).then(res => {
    comments.value = res.data.records || []
    comments.value.forEach(comment => loadRepliesForComment(comment))
  })
}
const showDetail = (comment) =>{
  currentComment.value = comment
  postId.value = comment.postId || ''
  drawerVisible.value = true
}
const currentContent = computed(() => {
  if (!currentComment.value) return null
  return contents.value.find(content => content.postId === currentComment.value.postId)
})
const resetCommentForm = () => {
  commentForm.value = {
    commentContent: '',
    rating: 0,
    envScore: 0,
    tasteScore: 0,
    serviceScore: 0,
    image: '',
    video: ''
  }
  imageUrl.value = ''
  videoUrl.value = ''
}
const getMerchantPostComments = () => {
  getMerchantPostComments1(merchantId).then(res => {
    merchantPostComments.value = res.data
  })
}
const handleDeleteComment = (commentId) => {
  ElMessageBox.confirm('确定要删除这条评论吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    deleteComment(commentId).then(res => {
      if (res.data) {
        ElMessage.success('删除成功')
        getComments() // 删除后刷新评论列表
      } else {
        ElMessage.error(res.message || '删除失败')
      }
    }).catch(() => {
      ElMessage.error('删除请求失败')
    })
  }).catch(() => {
  })
}
onMounted(() => {
  getContents()
  getMerchantInfo()
  getComments()

})
const replyDialogVisible = ref(false)
const replyContent = ref('')
const replyingComment = ref(null)

const handleReplyClick = (comment) => {
  replyingComment.value = comment
  replyContent.value = ''
  replyDialogVisible.value = true
}

const submitReply = () => {
  if (!replyContent.value.trim()) {
    ElMessage.warning("回复内容不能为空")
    return
  }

  const replyData = {
    commentId: replyingComment.value.commentId,
    replyTo: replyingComment.value.userId, // 被回复人
    userId: userInfoStore.userInfo.userId,
    replyContent: replyContent.value
  }

  addReply(replyData).then(res => {
    if (res.data) {
      ElMessage.success("回复成功")
      replyDialogVisible.value = false
    } else {
      ElMessage.error(res.message || "回复失败")
    }
  }).catch(() => {
    ElMessage.error("回复请求异常")
  })
}

const toLike = (row) => {
  addLikeCount(row).then(res => {
    if (res.data) {
      ElMessage.success('点赞成功')
      getContents() // 刷新内容列表
    } else {
      ElMessage.error('点赞失败，请稍后重试')
    }
  }).catch(() => {
    ElMessage.error('点赞请求异常')
  })
}

getMerchantPostComments ()
getUsers()
</script>

<template>
  <div>
    <h1>商家详情</h1>
    <el-card class="page-container">
      <template #header>
        <div class="header">
          <span>商家信息</span>
        </div>
      </template>
      <div>
        <p><strong>商家名称:</strong> {{ merchant.merchantName }}</p>
        <p><strong>商家描述:</strong> {{ merchant.description }}</p>
        <p><strong>商家标签:</strong> {{ merchant.tag }}</p>
        <p><strong>联系电话:</strong> {{ merchant.contactPhone }}</p>
        <p><strong>联系邮箱:</strong> {{ merchant.contactEmail }}</p>
        <p><strong>商家地址:</strong> {{ merchant.address }}</p>
        <p><strong>商家评分:</strong> {{ merchant.avgRating }}</p>
        <p><strong>人均消费:</strong> {{ merchant.priceLevel }}</p>
        <p><strong>营业时间:</strong> {{ merchant.businessHours }}</p>
      </div>
    </el-card>
  </div>
  <div>
    <h1>商家发布内容</h1>
    <el-table :data="contents" style="width: 100%">
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="content" label="内容" />
      <el-table-column prop="image" label="图片">
        <template #default="scope">
          <img height="100" :src="scope.row.imageUrl" alt="" />
        </template>
      </el-table-column>
      <el-table-column prop="video" label="视频">
        <template #default="scope">
          <video height="100" :src="scope.row.videoUrl" controls />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button type="primary" size="small" @click="showDetail(scope.row)">查看详情</el-button>
            <img src="../../assets/islike.png"  alt="" class="like" @click="toLike(scope.row)"/>
        </template>
      </el-table-column>
    </el-table>
  </div>

  <div>
    <h1>评论区</h1>
    <el-button plain type="primary" @click="dialogVisible = true">发布评论</el-button>
    <el-dialog v-model="dialogVisible" title="发布评论" width="300px" @close="resetCommentForm">
      <el-form :model="commentForm" label-width="100px">
        <el-form-item label="评论内容">
          <el-input v-model="commentForm.commentContent" type="textarea" rows="3" placeholder="请输入评论内容" />
        </el-form-item>
        <el-form-item label="总评分">
          <el-rate v-model="commentForm.rating" />
        </el-form-item>
        <el-form-item label="环境评分">
          <el-rate v-model="commentForm.envScore" />
        </el-form-item>
        <el-form-item label="口味评分">
          <el-rate v-model="commentForm.tasteScore" />
        </el-form-item>
        <el-form-item label="服务评分">
          <el-rate v-model="commentForm.serviceScore" />
        </el-form-item>
        <el-form-item label="上传图片">
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
        <el-form-item label="上传视频">
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
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false; resetCommentForm()">取消</el-button>
        <el-button type="primary" @click="handleCommentSubmit">确认</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="replyDialogVisible" title="回复评论" width="400px" @close="resetCommentForm">
      <el-form>
        <el-form-item label="回复内容">
          <el-input
              v-model="replyContent"
              type="textarea"
              rows="3"
              placeholder="请输入回复内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="replyDialogVisible = false; resetCommentForm()">取消</el-button>
        <el-button type="primary" @click="submitReply">提交</el-button>
      </template>
    </el-dialog>
    <el-table :data="comments" style="width: 100%">
      <el-table-column label="用户" width="120">
        <template #default="scope">
          <div style="display: flex; flex-direction: column; align-items: center;">
            <img :src="users.find(user => user.userId === scope.row.userId)?.avatar" class="avatar" alt="" width="60px" />
            <span>{{ scope.row.userName }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="评论详情" min-width="250">
        <template #default="scope">
          <div style="display: flex; flex-direction: column; height: 100%;">
            <div style="margin-bottom: 8px;">{{ scope.row.commentContent }}</div>

            <div
                v-if="commentRepliesMap[scope.row.commentId]?.length"
                v-for="reply in commentRepliesMap[scope.row.commentId]"
                :key="reply.id"
                style="margin-left: 20px; font-size: 13px; color: #666;"
            >
              <div>
                <span style="color: green;">回复：</span>
                <strong>{{ users.find(user => user.userId === reply.userId)?.userName || '用户' }}</strong>：
                {{ reply.replyContent }}
              </div>
            </div>

            <div style="display: flex; flex-direction: column; justify-content: space-between; font-size: 12px; color: #999;">
              <div>
                总评分：{{ scope.row.rating }} ⭐ |
                环境：{{ scope.row.envScore }} ⭐ |
                口味：{{ scope.row.tasteScore }} ⭐ |
                服务：{{ scope.row.serviceScore }} ⭐
              </div>
              <span>发表于：{{ scope.row.createTime }}</span>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="图片" width="150">
        <template #default="scope">
          <img
              v-if="scope.row.image && scope.row.image.trim() !== ''"
              :src="scope.row.image"
              alt="评论图片"
              style="max-height: 100px;"
          />
        </template>
      </el-table-column>

      <el-table-column label="" width="30">
        <template #default>
        </template>
      </el-table-column>

      <el-table-column label="视频" width="180">
        <template #default="scope">
          <video
              v-if="scope.row.video && scope.row.video.trim() !== ''"
              :src="scope.row.video"
              controls
              style="max-height: 100px;"
          ></video>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="scope">
          <el-button
              v-if="scope.row.userId === userInfoStore.userInfo.userId"
              type="danger"
              size="small"
              @click="handleDeleteComment(scope.row.commentId)"
          >
            删除
          </el-button>
          <el-button
              v-if="scope.row.userId !== userInfoStore.userInfo.userId"
              type="primary"
              size="small"
              @click="handleReplyClick(scope.row)"
          >
            回复
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
  <el-drawer
      v-model="drawerVisible"
      title="动态详情"
      direction="rtl"
      size="43%"
      @close="handleDrawerClose"
  >
    <div class="drawer-scroll-wrapper">
      <div v-if="currentComment">
        <h1>{{ currentContent?.title }}</h1>
        <p>{{ currentContent?.content }}</p>
        <img height="200px" :src="currentContent?.imageUrl" alt="" />
        <video v-if="currentContent?.videoUrl" height="200" :src="currentContent.videoUrl" controls></video>
        <p style="font-size: 14px;"><img src="../../assets/islike.png" height="20px" width="20px"/>点赞量：{{ currentContent?.likeCount }}</p>
        <br>
        <h2>评论</h2>
        <el-button plain type="primary" @click="dialogVisible = true">发布评论</el-button>
        <el-dialog v-model="dialogVisible" title="发布评论" width="300px">
          <el-form :model="commentForm" label-width="100px">
            <el-form-item label="评论内容">
              <el-input v-model="commentForm.commentContent" type="textarea" rows="3" placeholder="请输入评论内容" />
            </el-form-item>
            <el-form-item label="总评分">
              <el-rate v-model="commentForm.rating" />
            </el-form-item>
            <el-form-item label="环境评分">
              <el-rate v-model="commentForm.envScore" />
            </el-form-item>
            <el-form-item label="口味评分">
              <el-rate v-model="commentForm.tasteScore" />
            </el-form-item>
            <el-form-item label="服务评分">
              <el-rate v-model="commentForm.serviceScore" />
            </el-form-item>
            <el-form-item label="上传图片">
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
            <el-form-item label="上传视频">
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
          </el-form>
          <template #footer>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleCommentSubmit">确认</el-button>
          </template>
        </el-dialog>
        <div
            v-for="comment in merchantPostComments.filter(c => c.postId === currentContent?.postId)"
            :key="comment.id"
            class="comment-item"
        >
          <img
              :src="users.find(user => user.userId === comment.userId)?.avatar"
              class="avatar"
              alt=""
          />
          <div class="comment-content">
            <div class="username">{{ users.find(user => user.userId === comment.userId)?.userName }}</div>
            <div class="text">{{ comment.commentContent }}</div>
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
img {
  max-height: 100px;
}
video {
  width: 100%;
  height: auto;
  max-height: 150px;
}


.el-table .cell {
  white-space: nowrap;
}
.drawer-scroll-wrapper {
  height: 100%;
  overflow-y: auto;
  padding: 0 100px;
}
.comment-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  margin-bottom: 16px;
  border-radius: 8px;
  background-color: #f9f9f9;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.comment-item .avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  margin-right: 16px;
  object-fit: cover;
  border: 1px solid #ccc;
}

.comment-content {
  flex: 1;
}

.comment-content .username {
  font-weight: bold;
  font-size: 16px;
  color: #333;
  margin-bottom: 4px;
}

.comment-content .text {
  font-size: 14px;
  color: #555;
  margin-bottom: 8px;
}

.comment-content .time {
  font-size: 12px;
  color: #999;
}

.like{
  width: 20px;
  height: 20px;
  margin-left: 40px;
  cursor: pointer;
}
</style>
