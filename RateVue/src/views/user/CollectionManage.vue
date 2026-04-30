<template>
  <div class="merchant-list-page">
    <el-card>
      <div style="margin-bottom: 16px">
        <el-button type="danger" :disabled="selectedMerchants.length === 0" @click="batchRemoveFavorite">
          批量取消收藏 ({{ selectedMerchants.length }})
        </el-button>
      </div>

      <el-table
          :data="merchants"
          style="width: 100%"
          @selection-change="handleSelectionChange"
          @select="handleSelect"
          @select-all="handleSelectAll"
      >

        <el-table-column type="selection" width="55" />
        <el-table-column prop="merchantName" label="名称" width="150" />
        <el-table-column prop="description" label="描述" width="150" />
        <el-table-column prop="tag" label="标签" width="80" />
        <el-table-column prop="contactPhone" label="联系电话" width="120" />
        <el-table-column prop="address" label="地址" width="180" />
        <el-table-column prop="avgRating" label="评分" width="80" />
        <el-table-column prop="priceLevel" label="人均消费" width="80" />
        <el-table-column prop="businessHours" label="营业时间" width="120" />
        <el-table-column label="操作" width="300">
          <template #default="scope">
            <el-button type="primary" size="small" @click="viewMerchantDetails(scope.row)">查看详情</el-button>
            <el-button type="primary" size="small" @click="updateFavoriteTag(scope.row)">修改标签</el-button>
            <el-button type="danger" size="small" @click="removeFavoriteById(scope.row)">取消收藏</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
          v-model:current-page="searchForm.pageNum"
          v-model:page-size="searchForm.pageSize"
          :page-sizes="[5, 10, 20, 50]"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="pageNoChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserInfoStore } from '@/stores/userInfo';
import {getUserCollect, getFavoriteByUserAndMerchant, deleteFavorite, updateFavorite} from "@/api/user";
import {ElMessage, ElMessageBox} from "element-plus";

const userInfoStore = useUserInfoStore();

const merchants = ref([])
const selectedMerchants = ref([])
const total = ref(0)

const searchForm = ref({
  userId: userInfoStore.userInfo.userId || '',
  minScore: '',
  maxScore: '',
  minPrice: '',
  maxPrice: '',
  sortBy: '',
  pageNum: 1,
  pageSize: 10
})

const handleSelectionChange = (selection) => {
  selectedMerchants.value = selection
}

const handleSelect = (selection, row) => {
}

const handleSelectAll = (selection) => {
}

const batchRemoveFavorite = async () => {
  try {

    await ElMessageBox.confirm(
        `确定要取消收藏这 ${selectedMerchants.value.length} 个商户吗？`,
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    const userId = userInfoStore.userInfo.userId
    const deletePromises = selectedMerchants.value.map(async merchant => {
      const res = await getFavoriteByUserAndMerchant(userId, merchant.merchantId)
      if (res.data && res.data.records.length > 0) {
        return deleteFavorite(res.data.records[0].favoriteId)
      }
      console.warn('未找到收藏记录:', merchant.merchantId)
      return Promise.resolve()
    })

    await Promise.all(deletePromises)
    ElMessage.success(`成功取消收藏 ${selectedMerchants.value.length} 个商户`)
    selectedMerchants.value = []
    search()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量取消收藏失败:', error)
      ElMessage.error('批量取消收藏失败')
    }
  }
}

const pageNoChange = (value) => {
  searchForm.pageNum = value
  search()
}

const handleSizeChange = (value) => {
  searchForm.pageSize = value
  search()
}

const search = async () => {
  const res = await getUserCollect(
      searchForm.value.userId,
      {
        pageNum: searchForm.value.pageNum,
        pageSize: searchForm.value.pageSize,
      }
  )
  merchants.value = res.data.records
  total.value = res.data.total
}

const removeFavoriteById = async (row) => {
  try {
    const userId = userInfoStore.userInfo.userId

    const res = await getFavoriteByUserAndMerchant(userId, row.merchantId)

    if (!res.data || res.data.records.length === 0) {
      console.warn('未找到收藏记录')
      ElMessage.warning('未找到收藏记录')
      return
    }

    const favoriteId = res.data.records[0].favoriteId

    await ElMessageBox.confirm(
        '确定要取消收藏该商户吗？',
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    await deleteFavorite(favoriteId)
    ElMessage.success('取消收藏成功')
    search()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('取消收藏失败')
    }
  }
}

const updateFavoriteTag = async (row) => {
  try {
    const userId = userInfoStore.userInfo.userId
    const res = await getFavoriteByUserAndMerchant(userId, row.merchantId)

    const favoriteId = res.data.records[0].favoriteId

    const { value: newTag } = await ElMessageBox.prompt(
        '请输入新的标签',
        '修改标签',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputValue: row.tag || '',
          inputPattern: /^[\u4e00-\u9fa5\w,]{1,8}$/,
          inputErrorMessage: '标签必须为1-8个字符且不能包含空格',
          inputPlaceholder: '请输入1-8个字符的标签'
        }
    )

    await updateFavorite(favoriteId, newTag)
    ElMessage.success('标签已更新')
    search()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('修改标签失败:', error)
      ElMessage.error('修改标签失败')
    }
  }
}

onMounted(() => {
  search()
})

import { useRouter } from 'vue-router'

const router = useRouter()

const viewMerchantDetails = (row) => {
  if (!row || !row.merchantId) {
    ElMessage.error('无效的商户信息')
    return
  }
  router.push({
    path: `/user/shop/${row.merchantId}`
  })
}
</script>

<style scoped>
.merchant-list-page {
  padding: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(232, 205, 178, 0.74);
  box-shadow: 0 18px 44px rgba(196, 101, 34, 0.08);
}

.category-row {
  margin-bottom: 12px;
}

.merchant-list-page :deep(.el-card),
.merchant-list-page :deep(.el-table) {
  border-radius: 18px;
  border-color: rgba(232, 205, 178, 0.74);
  box-shadow: none;
  overflow: hidden;
}

.merchant-list-page :deep(.el-table th.el-table__cell) {
  background: #fff7ed;
  color: #9a5a12;
}

.merchant-list-page :deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

.merchant-list-page :deep(.el-button--primary) {
  background: #d97706;
  border-color: #d97706;
}
</style>
