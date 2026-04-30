<script>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { format } from 'date-fns'
import {
  getUserList,
  updateUser,
  updateUserStatus,
  deleteUser,
  getUserLoginRecords,
  getUserPaymentRecords,
  getUserFavoriteRecords,
} from '@/api/user';

export default {
  components: {
    Plus
  },
  setup() {
    const searchQuery = ref('')
    const userList = ref([])
    const loading = ref(false)
    const currentPage = ref(1)
    const pageSize = ref(10)
    const total = ref(0)

    const detailDialogVisible = ref(false)
    const currentUser = ref(null)

    const editDialogVisible = ref(false)
    const editForm = ref(null)

    const fetchUserList = async () => {
      loading.value = true
      try {
        const res = await getUserList({
          pageNum: currentPage.value,
          pageSize: pageSize.value,
          query: searchQuery.value
        })

        userList.value = res.data.records;
        total.value = res.data.total;

      } catch (error) {
        ElMessage.error('获取用户列表失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }

    const handleSizeChange = (newSize) => {
      pageSize.value = newSize
      currentPage.value = 1
      fetchUserList()
    }

    const handlePageChange = (newPage) => {
      currentPage.value = newPage
      fetchUserList()
    }

    const handleSearch = () => {
      currentPage.value = 1
      fetchUserList()
    }

    const showUserDetail = (user) => {
      currentUser.value = user
      detailDialogVisible.value = true
    }

    const showEditDialog = (user) => {
      editForm.value = { ...user }
      editDialogVisible.value = true
    }

    const saveUserInfo = async () => {
      try {
        await updateUser(editForm.value)
        ElMessage.success('用户信息更新成功')
        editDialogVisible.value = false
        await fetchUserList()
      } catch (error) {
        ElMessage.error('更新用户信息失败: ' + error.message)
      }
    }

    const toggleUserStatus = async (user) => {
      const newStatus = user.userStatus === 'active' ? 'frozen' : 'active'
      const action = newStatus === 'frozen' ? '冻结' : '解冻'

      try {
        await ElMessageBox.confirm(
            `确定要${action}用户 ${user.userName} 吗?`,
            '提示',
            {
              confirmButtonText: '确定',
              cancelButtonText: '取消',
              type: 'warning'
            }
        )

        await updateUserStatus(user.userId, newStatus)
        user.userStatus = newStatus
        ElMessage.success(`用户已${action}`)
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(`${action}用户失败: ${error.message}`)
        }
      }
    }

    const confirmDelete = (user) => {
      ElMessageBox.confirm(
          `确定要永久删除用户 ${user.userName} 吗? 此操作不可恢复!`,
          '警告',
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'error'
          }
      ).then(async () => {
        try {
          await deleteUser(user.userId)
          ElMessage.success('用户已删除')
          await fetchUserList()
        } catch (error) {
          ElMessage.error('删除用户失败: ' + error.message)
        }
      }).catch(() => {})
    }

    const handleAvatarSuccess = (res) => {
      editForm.value.avatar = res.data.url
    }

    const beforeAvatarUpload = (file) => {
      const isImage = file.type.startsWith('image/')
      const isLt2M = file.size / 1024 / 1024 < 2

      if (!isImage) {
        ElMessage.error('只能上传图片文件!')
      }
      if (!isLt2M) {
        ElMessage.error('头像图片大小不能超过 2MB!')
      }

      return isImage && isLt2M
    }

    const formatStatus = (status) => {
      const statusMap = {
        active: '正常',
        frozen: '已冻结'
      }
      return statusMap[status] || status
    }

    const formatDate = (date) => {
      return date ? format(new Date(date), 'yyyy-MM-dd HH:mm:ss') : '无'
    }

    onMounted(() => {
      fetchUserList()
    })

    return {
      searchQuery,
      userList,
      loading,
      currentPage,
      pageSize,
      total,
      detailDialogVisible,
      currentUser,
      editDialogVisible,
      editForm,

      fetchUserList,
      handleSearch,
      handleSizeChange,
      handlePageChange,
      showUserDetail,
      showEditDialog,
      saveUserInfo,
      toggleUserStatus,
      confirmDelete,
      handleAvatarSuccess,
      beforeAvatarUpload,
      formatStatus,
      formatDate
    }
  }
}
</script>

<template>
  <div class="user-management">
    <div class="search-bar">
      <el-input
          v-model="searchQuery"
          placeholder="请输入昵称、电话或邮箱搜索"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
          style="width: 300px; margin-right: 10px"
      />
      <el-button type="primary" @click="handleSearch">搜索</el-button>
    </div>

    <el-table
        :data="userList"
        border
        style="width: 100%"
        v-loading="loading"
    >
      <el-table-column prop="userName" label="昵称" width="120" />
      <el-table-column prop="phone" label="电话" width="150" />
      <el-table-column prop="email" label="邮箱" width="200" />
      <el-table-column label="密码" width="150">
        <template #default="{ row }">
          {{ row.password ? '******' : '' }}
        </template>
      </el-table-column>
      <el-table-column label="头像" width="100">
        <template #default="{ row }">
          <el-avatar :src="row.avatar" v-if="row.avatar" />
          <span v-else>无头像</span>
        </template>
      </el-table-column>
      <el-table-column prop="userStatus" label="账号状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.userStatus === 'active' ? 'success' : 'danger'">
            {{ formatStatus(row.userStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showUserDetail(row)">详情</el-button>
          <el-button size="small" type="primary" @click="showEditDialog(row)">编辑</el-button>
          <el-button
              size="small"
              :type="row.userStatus === 'active' ? 'warning' : 'success'"
              @click="toggleUserStatus(row)"
          >
            {{ row.userStatus === 'active' ? '冻结' : '解冻' }}
          </el-button>
          <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
      />
    </div>

    <el-dialog v-model="detailDialogVisible" title="用户详细信息" width="50%">
      <div v-if="currentUser">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="昵称">{{ currentUser.userName }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ currentUser.phone }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ currentUser.email }}</el-descriptions-item>
          <el-descriptions-item label="密码">{{ currentUser.password }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatDate(currentUser.createTime) }}</el-descriptions-item>
          <el-descriptions-item label="账号状态">
            <el-tag :type="currentUser.userStatus === 'active' ? 'success' : 'danger'">
              {{ formatStatus(currentUser.userStatus) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-tabs type="border-card" style="margin-top: 20px">
          <el-tab-pane label="登录记录">
            <el-table :data="currentUser.loginRecords" height="250">
              <el-table-column prop="loginTime" label="登录时间" width="180" />
              <el-table-column prop="ip" label="IP地址" width="150" />
              <el-table-column prop="device" label="设备" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="消费记录">
            <el-table :data="currentUser.paymentRecords" height="250">
              <el-table-column prop="orderId" label="订单号" width="180" />
              <el-table-column prop="amount" label="金额" width="120" />
              <el-table-column prop="paymentTime" label="支付时间" width="180" />
              <el-table-column prop="status" label="状态" width="120" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="收藏记录">
            <el-table :data="currentUser.favoriteRecords" height="250">
              <el-table-column prop="itemName" label="收藏商家" />
              <el-table-column prop="favoriteTime" label="收藏时间" width="180" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑用户信息" width="40%">
      <el-form :model="editForm" label-width="100px" v-if="editForm">
        <el-form-item label="昵称">
          <el-input v-model="editForm.userName" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="editForm.password" type="password" show-password placeholder="留空则不修改" />
        </el-form-item>
        <el-form-item label="头像">
          <el-upload
              class="avatar-uploader"
              action="/api/file/upload"
              :show-file-list="false"
              :on-success="handleAvatarSuccess"
              :before-upload="beforeAvatarUpload"
          >
            <img v-if="editForm.avatar" :src="editForm.avatar" class="avatar" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUserInfo">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.user-management {
  padding: 20px;
}

.search-bar {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.avatar-uploader {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 100px;
  height: 100px;
}

.avatar-uploader:hover {
  border-color: var(--el-color-primary);
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100px;
  height: 100px;
  line-height: 100px;
  text-align: center;
}

.avatar {
  width: 100px;
  height: 100px;
  display: block;
}

.user-management {
  padding: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(203, 213, 225, 0.78);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
}

.search-bar {
  padding: 16px;
  margin-bottom: 18px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid rgba(203, 213, 225, 0.72);
}

.user-management :deep(.el-table) {
  border-radius: 18px;
  overflow: hidden;
}

.user-management :deep(.el-table th.el-table__cell) {
  background: #eef4ff;
  color: #1e3a8a;
}

.user-management :deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

.user-management :deep(.el-button--primary) {
  background: #3667ff;
  border-color: #3667ff;
}
</style>
