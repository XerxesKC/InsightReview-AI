<script setup lang="ts">
import {ref} from 'vue'
import {getComments1,deleteComment1,changeCommentStatus1} from "@/api/comment";
import {getUsers1} from "@/api/user";
import {ElMessage, ElMessageBox} from "element-plus";

const comments = ref([])
const getComments = () => {
  getComments1().then(res => {
    comments.value = res.data
  })
}

const users = ref([])
const getUsers = () =>{
  getUsers1().then(res => {
    users.value = res.data
  })
}

const deleteComment = (row) => {
  const comment = {
    commentId: row.commentId,
    userId: row.userId,
    commentContent: row.commentContent,
    image: row.image,
    video: row.video
  }
  ElMessageBox.confirm(
      '是否确认删除当前评论？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
  )
      .then(() => {
        deleteComment1(comment).then((res)=>{
          if(res.data){
            ElMessage({
              message: '删除成功',
              type: 'success'
            })
          }
          getComments()
        })
      })
      .catch(() => {
      })
}

const changeCommentStatus = (row) => {
  const comment = {
    commentId: row.commentId,
    userId: row.userId,
    commentContent: row.commentContent,
    image: row.image,
    video: row.video
  }
  ElMessageBox.confirm(
      '是否确认通过当前评论？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
  )
      .then(() => {
        changeCommentStatus1(comment).then((res)=>{
          if(res.data){
            ElMessage({
              message: '通过成功',
              type: 'success'
            })
          }
          getComments()
        })
      })
      .catch(() => {
      })
}
getComments()
getUsers()
</script>

<template>
  <div class="header">
    <el-table :data="comments" style="width: 100%" >
      <el-table-column label="用户">
        <template #default="scope">
          {{ users.find(user => user.userId === scope.row.userId)?.userName || '未知用户' }}
        </template>
      </el-table-column>
      <el-table-column label="评论内容">
        <template #default="scope">
          {{ scope.row.commentContent }}
        </template>
      </el-table-column>
      <el-table-column label="评论图片" >
        <template #default="scope">
          <img height="100" :src="scope.row.image" alt="">
        </template>
      </el-table-column>
      <el-table-column prop="video" label="视频" >
        <template #default="scope">
          <video height="100" :src="scope.row.video" controls v-if="scope.row.video"></video>
          <span v-else></span>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button type="success" @click="changeCommentStatus(scope.row)">通过</el-button>
          <el-button type="danger" @click="deleteComment(scope.row)">不通过</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.header{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(203, 213, 225, 0.78);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.header :deep(.el-table) {
  border-radius: 18px;
  overflow: hidden;
}

.header :deep(.el-table th.el-table__cell) {
  background: #eef4ff;
  color: #1e3a8a;
}

.header :deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

.header :deep(.el-button--success) {
  background: #3667ff;
  border-color: #3667ff;
}
</style>
