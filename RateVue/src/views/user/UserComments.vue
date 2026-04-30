<template>
  <div class="comment-manage-page">
    <el-card>
      <div style="margin-bottom: 16px">
        <el-button type="danger" :disabled="selectedComments.length === 0" @click="batchDeleteComments">
          批量删除评论 ({{ selectedComments.length }})
        </el-button>
      </div>

      <el-table
          :data="comments"
          @selection-change="handleSelectionChange"
          style="width: 100%">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="commentContent" label="评论内容" min-width="200" />
        <el-table-column label="评分">
          <template #default="scope">
            环境：{{ scope.row.envScore }} |
            口味：{{ scope.row.tasteScore }} |
            服务：{{ scope.row.serviceScore }}
            总：{{ scope.row.rating }}
          </template>
        </el-table-column>
        <el-table-column label="图片" width="100">
          <template #default="scope">
            <img v-if="scope.row.image" :src="scope.row.image" style="height: 60px;" />
          </template>
        </el-table-column>
        <el-table-column label="视频" width="100">
          <template #default="scope">
            <video v-if="scope.row.video" :src="scope.row.video" controls style="height: 60px;" />
          </template>
        </el-table-column>
        <el-table-column label="审核状态" width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.status === 'T'" type="success">审核通过</el-tag>
            <el-tag v-else-if="scope.row.status === 'F'" type="danger">未通过</el-tag>
            <el-tag v-else type="info">待审核</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="评论时间" width="160" />
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button type="danger" size="small" @click="deleteCommentById(scope.row.commentId)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
          v-model:current-page="pageNum"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserInfoStore } from '@/stores/userInfo'
import { searchUserComment, deleteComment } from '@/api/comment'

const userInfoStore = useUserInfoStore()

const comments = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(10)
const selectedComments = ref([])

const fetchComments = async () => {
  const res = await searchUserComment({
    userId: userInfoStore.userInfo.userId,
    pageNum: pageNum.value,
    pageSize: pageSize.value
  })
  comments.value = res.data.records || []
  total.value = res.data.total || 0
}

const deleteCommentById = async (commentId) => {
  try {
    await ElMessageBox.confirm('确定要删除该评论吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteComment(commentId)
    ElMessage.success('删除成功')
    fetchComments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error('删除失败')
    }
  }
}

const batchDeleteComments = async () => {
  try {
    await ElMessageBox.confirm(`确定删除这 ${selectedComments.value.length} 条评论吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await Promise.all(selectedComments.value.map(item => deleteComment(item.commentId)))
    ElMessage.success('批量删除成功')
    selectedComments.value = []
    fetchComments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const handleSelectionChange = (val) => {
  selectedComments.value = val
}

const handlePageChange = (val) => {
  pageNum.value = val
  fetchComments()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  fetchComments()
}

onMounted(() => {
  fetchComments()
})
</script>

<style scoped>
.comment-manage-page {
  padding: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(232, 205, 178, 0.74);
  box-shadow: 0 18px 44px rgba(196, 101, 34, 0.08);
}

.comment-manage-page :deep(.el-card),
.comment-manage-page :deep(.el-table) {
  border-radius: 18px;
  border-color: rgba(232, 205, 178, 0.74);
  box-shadow: none;
  overflow: hidden;
}

.comment-manage-page :deep(.el-table th.el-table__cell) {
  background: #fff7ed;
  color: #9a5a12;
}

.comment-manage-page :deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

.comment-manage-page :deep(.el-button--primary) {
  background: #d97706;
  border-color: #d97706;
}
</style>
