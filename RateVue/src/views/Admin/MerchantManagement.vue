<script setup>
import { ref, onMounted } from 'vue'
import { Search, View, Delete, Lock, Unlock } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getMerchantList,
  updateMerchant,
  verifyMerchant,
  toggleMerchantStatus,
  deleteMerchant,
  uploadMerchantImage
} from '@/api/merchant'


const searchQuery = ref('')
const merchants = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const detailDialogVisible = ref(false)
const currentMerchant = ref({})
const isEditing = ref(false)
const detailForm = ref(null)

const convertVerificationStatus = (status) => {
  const statusMap = {
    0: '审核不通过',
    1: '审核中',
    2: '审核通过'
  }
  return statusMap[status] || status
}

const convertMerchantStatus = (status) => {
  const statusMap = {
    active: '正常',
    frozen: '已冻结'
  }
  return statusMap[status] || status
}

const fetchMerchants = async () => {
  loading.value = true
  try {
    const params = {
      pageNum: currentPage.value,
      pageSize: pageSize.value,
      searchQuery: searchQuery.value
    }
    const response = await getMerchantList(params)
    merchants.value = response.data.records.map(merchant => ({
      ...merchant,
      verificationStatus: convertVerificationStatus(merchant.verificationStatus),
      merchantStatus: convertMerchantStatus(merchant.merchantStatus)
    }))
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('获取商家列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchMerchants()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  fetchMerchants()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchMerchants()
}

const handleViewDetail = (merchant) => {
  currentMerchant.value = JSON.parse(JSON.stringify(merchant))
  detailDialogVisible.value = true
  isEditing.value = false
}

const startEditing = () => {
  isEditing.value = true
}

const cancelEditing = () => {
  isEditing.value = false
  const original = merchants.value.find(m => m.id === currentMerchant.value.id)
  if (original) {
    currentMerchant.value = JSON.parse(JSON.stringify(original))
  }
}

const saveChanges = async () => {
  try {
    loading.value = true

    const payload = {
      ...currentMerchant.value,
      verificationStatus: convertStatusToBackendFormat(currentMerchant.value.verificationStatus),
      merchantStatus: currentMerchant.value.merchantStatus === '正常' ? 'active' : 'frozen'
    }

    delete payload._id
    delete payload._index

    const response = await updateMerchant(payload)

    const index = merchants.value.findIndex(m => m.merchantId === currentMerchant.value.merchantId)
    if (index !== -1) {
      merchants.value[index] = {
        ...response.data,
        verificationStatus: convertStatusToFrontendFormat(response.data.verificationStatus),
        merchantStatus: response.data.merchantStatus === 'active' ? '正常' : '已冻结'
      }
    }

    isEditing.value = false
    ElMessage.success('商家信息更新成功')
  } catch (error) {
    handleApiError(error, '保存商家信息')
  } finally {
    loading.value = false
  }
}

const convertStatusToBackendFormat = (status) => {
  const map = {
    '审核不通过': 0,
    '审核中': 1,
    '审核通过': 2
  }
  return map[status] ?? 1
}

const convertStatusToFrontendFormat = (status) => {
  const map = {
    0: '审核不通过',
    1: '审核中',
    2: '审核通过'
  }
  return map[status] ?? '审核中'
}

const handleVerify = async (merchant) => {
  if (merchant.verificationStatus === 1) {
    try {
      const { value } = await ElMessageBox.prompt('请输入审核意见', '审核商家', {
        confirmButtonText: '通过',
        cancelButtonText: '不通过',
        inputPlaceholder: '可选：审核通过意见'
      });

      await verifyMerchant({
        merchantId: merchant.merchantId,
        status: 2,
        review: value || '审核通过'
      });
      merchant.verificationStatus = 2;
      merchant.review = value || '审核通过';
      ElMessage.success('审核通过');

    } catch (error) {
      if (error === 'cancel') {
        try {
          const { value: rejectReason } = await ElMessageBox.prompt(
              '请输入不通过原因',
              '审核不通过',
              {
                confirmButtonText: '确认拒绝',
                cancelButtonText: '取消',
                inputPlaceholder: '必须填写详细原因（至少10个字）',
                inputValidator: (val) => val && val.trim().length >= 10 || '原因不能少于10个字'
              }
          );

          await verifyMerchant({
            merchantId: merchant.merchantId,
            status: 0,
            review: rejectReason
          });
          merchant.verificationStatus = 0;
          merchant.review = rejectReason;
          ElMessage.warning('已拒绝审核');

        } catch (innerError) {
          if (innerError === 'cancel') {
            ElMessage.info('已取消拒绝操作');
          } else {
            ElMessage.error(`拒绝操作失败: ${innerError.message}`);
          }
          return;
        }
      } else {
        ElMessage.error(`审核失败: ${error.message}`);
        return;
      }
    }
  } else {
    try {
      await verifyMerchant({
        merchantId: merchant.merchantId,
        status: 1,
        review: ''
      });
      merchant.verificationStatus = 1;
      merchant.review = '';
      ElMessage.info('已重新提交审核');
    } catch (error) {
      ElMessage.error(`重新提交审核失败: ${error.message}`);
    }
  }

  try {
    await fetchMerchants();
  } catch (error) {
    console.error('刷新列表失败:', error);
  }
}

const handleToggleStatus = async (merchant) => {
  try {
    const isActive = ['active', '正常', '1'].includes(merchant.merchantStatus)

    await ElMessageBox.confirm(
        `确定要${isActive ? '冻结' : '解冻'}商家 "${merchant.merchantName}" 吗?`,
        `${isActive ? '冻结' : '解冻'}商家`
    )

    loading.value = true
    const newStatus = isActive ? 'frozen' : 'active'

    await toggleMerchantStatus({
      merchantId: merchant.merchantId,
      status: newStatus
    })

    const merchantIndex = merchants.value.findIndex(m => m.merchantId === merchant.merchantId)
    if (merchantIndex !== -1) {
      merchants.value = [
        ...merchants.value.slice(0, merchantIndex),
        { ...merchants.value[merchantIndex], merchantStatus: newStatus },
        ...merchants.value.slice(merchantIndex + 1)
      ]
    }
    await fetchMerchants()

    ElMessage.success(`${newStatus === 'active' ? '解冻' : '冻结'}成功`)
  } catch (error) {
    if (error !== 'cancel') {
      const errorMsg = error.response?.data?.message ||
          error.response?.statusText ||
          error.message
      ElMessage.error(`操作失败: ${errorMsg}`)
    }
  } finally {
    loading.value = false
  }
}

const handleDelete = async (merchant) => {
  try {
    await ElMessageBox.confirm(
        `确定要删除商家 "${merchant.merchantName}" 吗? 此操作不可恢复!`,
        '删除商家',
        { type: 'error' }
    )

    loading.value = true
    await deleteMerchant(merchant.merchantId)
    merchants.value = merchants.value.filter(m => m.merchantId !== merchant.merchantId)
    total.value -= 1
    ElMessage.success('删除成功')

    if (merchants.value.length === 0 && currentPage.value > 1) {
      currentPage.value -= 1
      await fetchMerchants()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  } finally {
    loading.value = false
  }
}

const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过5MB!')
  }

  return isImage && isLt5M
}

const handleCoverImageChange = async (file) => {
  try {
    const response = await uploadMerchantImage(file.raw)
    currentMerchant.value.coverImage = response.data.url
    ElMessage.success('封面图片上传成功')
  } catch (error) {
    ElMessage.error('图片上传失败: ' + error.message)
  }
}

const handleLicenseChange = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    currentMerchant.value.businessLicense = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

const handleHygienicLicenseChange = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    currentMerchant.value.hygienicLicense = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

const getStatusTagType = (status) => {
  const statusText = convertVerificationStatus(status)
  const map = {
    '审核中': 'info',
    '审核通过': 'success',
    '审核不通过': 'danger'
  }
  return map[statusText] || ''
}

const getVerifyButtonText = (merchant) => {
  const map = {
    '审核中': '审核商家',
    '审核通过': '重新审核',
    '审核不通过': '重新审核'
  }
  return map[merchant.verificationStatus] || '审核'
}

onMounted(() => {
  fetchMerchants()
})
</script>

<template>
  <div class="merchant-management">
    <el-card class="search-card">
      <div class="search-container">
        <el-input
            v-model="searchQuery"
            placeholder="请输入商家名称或联系方式"
            class="search-input"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button
                :icon="Search"
                @click="handleSearch"
                aria-label="搜索"
            />
          </template>
        </el-input>
      </div>
    </el-card>

    <el-card class="table-card">
      <el-table
          :data="merchants"
          border
          stripe
          style="width: 100%"
          v-loading="loading"
      >
        <el-table-column prop="merchantName" label="商家名称" width="180" />
        <el-table-column prop="tag" label="标签" width="120" />
        <el-table-column prop="contactPhone" label="联系电话" width="120" />
        <el-table-column prop="contactEmail" label="联系邮箱" width="180" />
        <el-table-column prop="verificationStatus" label="认证状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.verificationStatus)">
              {{ convertVerificationStatus(row.verificationStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="merchantStatus" label="账号状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.merchantStatus === '正常' ? 'success' : 'danger'">
              {{ convertMerchantStatus(row.merchantStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button
                size="small"
                @click="handleViewDetail(row)"
                :icon="View"
                aria-label="查看详情"
            >
              详情
            </el-button>
            <el-button
                size="small"
                :type="row.merchantStatus === '正常' ? 'warning' : 'success'"
                @click="handleToggleStatus(row)"
                :icon="row.merchantStatus === '正常' ? Lock : Unlock"
                :aria-label="row.merchantStatus === '正常' ? '冻结账号' : '解冻账号'"
            >
              {{ row.merchantStatus === '正常' ? '冻结' : '解冻' }}
            </el-button>
            <el-button
                size="small"
                type="danger"
                @click="handleDelete(row)"
                :icon="Delete"
                aria-label="删除商家"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog
        v-model="detailDialogVisible"
        :title="currentMerchant.merchantName + ' - 商家详情'"
        width="70%"
    >
      <el-form
          ref="detailForm"
          :model="currentMerchant"
          label-width="120px"
          :disabled="!isEditing"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="商家名称">
              <el-input v-model="currentMerchant.merchantName" />
            </el-form-item>
            <el-form-item label="商家密码">
              <el-input v-model="currentMerchant.merchantPassword" show-password />
            </el-form-item>
            <el-form-item label="商家标签">
              <el-input v-model="currentMerchant.tag" />
            </el-form-item>
            <el-form-item label="联系电话">
              <el-input v-model="currentMerchant.contactPhone" />
            </el-form-item>
            <el-form-item label="联系邮箱">
              <el-input v-model="currentMerchant.contactEmail" />
            </el-form-item>
            <el-form-item label="商家描述">
              <el-input
                  v-model="currentMerchant.description"
                  type="textarea"
                  :rows="3"
              />
            </el-form-item>
            <el-form-item label="地址">
              <el-input v-model="currentMerchant.address" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="认证状态">
              <el-select v-model="currentMerchant.verificationStatus">
                <el-option :value="0" label="审核不通过" />
                <el-option :value="1" label="审核中" />
                <el-option :value="2" label="审核通过" />
              </el-select>
            </el-form-item>
            <el-form-item label="账号状态">
              <el-select v-model="currentMerchant.merchantStatus">
                <el-option value="active" label="正常" />
                <el-option value="frozen" label="已冻结" />
              </el-select>
            </el-form-item>
            <el-form-item label="营业时间">
              <el-input v-model="currentMerchant.businessHours" />
            </el-form-item>
            <el-form-item label="平均评分">
              <el-input-number
                  v-model="currentMerchant.avgRating"
                  :min="0"
                  :max="5"
                  :step="0.1"
              />
            </el-form-item>
            <el-form-item label="人均消费">
              <el-input-number
                  v-model="currentMerchant.priceLevel"
                  :min="0"
                  :precision="2"
              />
            </el-form-item>
            <el-form-item label="注册时间">
              <el-date-picker
                  v-model="currentMerchant.createTime"
                  type="datetime"
                  disabled
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="封面图片">
              <el-image
                  style="width: 100%; height: 200px"
                  :src="currentMerchant.coverImage"
                  fit="contain"
              />
              <el-upload
                  v-if="isEditing"
                  action="#"
                  :show-file-list="false"
                  :before-upload="beforeImageUpload"
                  @change="handleCoverImageChange"
              >
                <el-button type="primary">更换封面</el-button>
              </el-upload>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="营业执照">
              <el-image
                  style="width: 100%; height: 200px"
                  :src="currentMerchant.businessLicense"
                  fit="contain"
              />
              <el-upload
                  v-if="isEditing"
                  action="#"
                  :show-file-list="false"
                  :before-upload="beforeImageUpload"
                  @change="handleLicenseChange"
              >
                <el-button type="primary">更换执照</el-button>
              </el-upload>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="卫生许可证">
          <el-image
              style="width: 100%; height: 200px"
              :src="currentMerchant.hygienicLicense"
              fit="contain"
          />
          <el-upload
              v-if="isEditing"
              action="#"
              :show-file-list="false"
              :before-upload="beforeImageUpload"
              @change="handleHygienicLicenseChange"
          >
            <el-button type="primary">更换许可证</el-button>
          </el-upload>
        </el-form-item>

        <el-form-item label="位置坐标">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-input-number
                  v-model="currentMerchant.longitude"
                  :step="0.000001"
                  :precision="6"
                  controls-position="right"
              />
              <span style="margin-left: 10px">经度</span>
            </el-col>
            <el-col :span="12">
              <el-input-number
                  v-model="currentMerchant.latitude"
                  :step="0.000001"
                  :precision="6"
                  controls-position="right"
              />
              <span style="margin-left: 10px">纬度</span>
            </el-col>
          </el-row>
        </el-form-item>

        <el-form-item label="审核信息">
          <el-input
              v-model="currentMerchant.review"
              type="textarea"
              :rows="3"
              :disabled="true"
          placeholder="暂无审核信息"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button v-if="!isEditing" type="primary" @click="startEditing">
            编辑
          </el-button>
          <template v-else>
            <el-button @click="cancelEditing">取消</el-button>
            <el-button type="primary" @click="saveChanges">保存</el-button>
          </template>
          <el-button
              v-if="!isEditing"
              type="warning"
              @click="handleVerify(currentMerchant)"
          >
            {{ getVerifyButtonText(currentMerchant) }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.merchant-management {
  padding: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(203, 213, 225, 0.78);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
}

.search-card {
  margin-bottom: 20px;
  border-radius: 18px;
  border-color: rgba(203, 213, 225, 0.72);
  box-shadow: none;
}

.search-container {
  display: flex;
}

.search-input {
  width: 400px;
}

.table-card {
  margin-bottom: 20px;
  border-radius: 18px;
  border-color: rgba(203, 213, 225, 0.72);
  box-shadow: none;
  overflow: hidden;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
}

.merchant-management :deep(.el-table th.el-table__cell) {
  background: #eef4ff;
  color: #1e3a8a;
}

.merchant-management :deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

.merchant-management :deep(.el-button--primary) {
  background: #3667ff;
  border-color: #3667ff;
}
</style>
