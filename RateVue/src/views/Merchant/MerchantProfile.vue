<script setup lang="ts">
import { useRouter } from 'vue-router'
import {useMerchantInfoStore} from "@/stores/merchantInfo";
import {getCurrentMerchant} from "@/api/merchant";
import {getCurrentCategoryName} from "@/api/category";
import {updateMerchant} from "@/api/merchant";
import {ElMessage} from "element-plus";
import {
  Clock,
  Document,
  Edit,
  Eleme,
  InfoFilled, Iphone,
  Location, Message,
  Money,
  Plus,
  Postcard,
  Tickets
} from "@element-plus/icons-vue";
import {onMounted, reactive, ref} from "vue";
import { Close, Check } from "@element-plus/icons-vue";

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

let currentCategory = ref('')
const getCategoryName = (categoryId) => {
  getCurrentCategoryName(categoryId.value).then(res => {
    if (res.data) {
      currentCategory.value =  res.data
    } else {
      ElMessage.error("获取商家类别失败")
      return ''
    }
  })
}

const imageUrl1=ref(merchantInfoStore.merchantInfo.coverImage)
const imageUrl2=ref(merchantInfoStore.merchantInfo.businessLicense)
const imageUrl3=ref(merchantInfoStore.merchantInfo.hygienicLicense)
getMerchantInfo()
let currentCategoryId = ref(merchantInfoStore.merchantInfo.categoryId)


import {ElMessageBox } from 'element-plus'
import type { Action } from 'element-plus'
const merchant = reactive({
  merchantId: merchantInfoStore.merchantInfo.merchantId,
  merchantName: merchantInfoStore.merchantInfo.merchantName,
  description: merchantInfoStore.merchantInfo.description,
  categoryId: '',
  tag: merchantInfoStore.merchantInfo.tag,
  contactPhone: merchantInfoStore.merchantInfo.contactPhone,
  contactEmail: merchantInfoStore.merchantInfo.contactEmail,
  address: merchantInfoStore.merchantInfo.address,
  coverImage: merchantInfoStore.merchantInfo.coverImage,
  businessLicense: merchantInfoStore.merchantInfo.businessLicense,
  hygienicLicense: merchantInfoStore.merchantInfo.hygienicLicense,
  verificationStatus: merchantInfoStore.merchantInfo.verificationStatus,
  businessHours: merchantInfoStore.merchantInfo.businessHours,
  priceLevel: merchantInfoStore.merchantInfo.priceLevel,
  merchantPassword: merchantInfoStore.merchantInfo.merchantPassword,
  review: merchantInfoStore.merchantInfo.review,
})

let parentList=ref([])
const childrenList=ref([])
const grandList=ref([])
const parentId=ref('')
const childrenId=ref('')
const grandId=ref('')
function getParentList() {

  parentList.value = [
    { parentId: 1, parentName: "餐饮" },
    { parentId: 2, parentName: "娱乐" },
    { parentId: 3, parentName: "购物" },
  ];


  if (parentId.value == '1') {
    childrenList.value = [
      { childrenId: 4, childrenName: "西餐" },
      { childrenId: 5, childrenName: "中餐" },
    ];
  } else if (parentId.value == '2') {
    childrenList.value = [
      { childrenId: 12, childrenName: "电影院" },
      { childrenId: 15, childrenName: "KTV" },
    ];
  }
  merchant.categoryId = parentId.value;
}
function getChildrenList() {


  if (childrenId.value == '4') {
    grandList.value = [
      { grandId: 9, grandName: "法式" },
      { grandId: 10, grandName: "意式" },
      { grandId: 11, grandName: "美式" },
    ];
  } else if (childrenId.value == '5') {
    grandList.value = [
      { grandId: 6, grandName: "川菜" },
      { grandId: 7, grandName: "鲁菜" },
      { grandId: 8, grandName: "粤菜" },
    ];
  } else if (childrenId.value == '12') {
    grandList.value = [
      { grandId: 13, grandName: "IMAX厅" },
      { grandId: 14, grandName: "普通厅" },
    ];
  } else if (childrenId.value == '15') {
    grandList.value = [
      { grandId: 16, grandName: "小" },
      { grandId: 17, grandName: "中" },
      { grandId: 18, grandName: "大" },
    ];
  }
  if (grandId.value == '') {
    merchant.categoryId = childrenId.value;
  } else {
    merchant.categoryId = grandId.value;
  }
}
getParentList();

const handleCoverImageSuccess = (response, uploadFile) => {
  imageUrl1.value = URL.createObjectURL(uploadFile.raw)
  merchant.coverImage = response.data.url
}
const handleBusinessLicenseSuccess = (response, uploadFile) => {
  imageUrl2.value = URL.createObjectURL(uploadFile.raw)
  merchant.businessLicense = response.data.url
}
const handleHygienicLicenseSuccess = (response, uploadFile) => {
  imageUrl3.value = URL.createObjectURL(uploadFile.raw)
  merchant.hygienicLicense = response.data.url
}

const startTime = ref<String>('')
const endTime = ref<String>('')
function getBusinessHours(){
  if (!startTime.value || !endTime.value) {
    return;
  }
  merchant.businessHours = `${startTime.value}-${endTime.value}`;
}
const password = ref(merchantInfoStore.merchantInfo.merchantPassword)
function checkPassword() {
  if (merchant.merchantPassword !== password.value) {
    ElMessage({
      message: '两次输入的密码不一致',
      type: 'error',
    })
  }
}
const isShow = ref(false)
const showEditDialog = () => {
  isShow.value = true
}

const changeMerchant = () => {
  merchant.verificationStatus = '1'
  if (merchant.merchantName === '') {
    ElMessage.error('商家名称不能为空')
    return
  }
  if (merchant.merchantPassword === '') {
    ElMessage.error('商家密码不能为空')
    return
  }
  if (merchant.description === '') {
    ElMessage.error('商家描述不能为空')
    return
  }
  if (merchant.categoryId === '') {
    ElMessage.error('请选择商家类别')
    return
  }
  if (merchant.tag === '') {
    ElMessage.error('商家标签不能为空')
    return
  }
  if (merchant.contactPhone === '') {
    ElMessage.error('商家电话不能为空')
    return
  }
  if (merchant.contactEmail === '') {
    ElMessage.error('商家邮箱不能为空')
    return
  }
  if (merchant.address === '') {
    ElMessage.error('商家地址不能为空')
    return
  }
  if (merchant.coverImage === '') {
    ElMessage.error('请上传商家封面图片')
    return
  }
  if (merchant.businessLicense === '') {
    ElMessage.error('请上传商家营业执照图片')
    return
  }
  if (merchant.hygienicLicense === '') {
    ElMessage.error('请上传商家卫生许可证图片')
    return
  }
  if (merchant.businessHours === '') {
    ElMessage.error('请设置商家的营业时间')
    return
  }
  if (merchant.priceLevel === '') {
    ElMessage.error('请设置商家的平均价格')
    return
  }
  merchant.verificationStatus = '1'
  updateMerchant(merchant).then(res => {
      if (res.data) {
        ElMessage.success('修改成功,下次登录自动更新商家信息');
        isShow.value = false;
        getMerchantInfo();
      } else {
        ElMessage.error('修改失败，请稍后再试');
      }
    })
  changeVerificationState()
  router.push({ path: '/login' })
}

let verificationState = ref({})
const changeVerificationState = () => {
  const state = merchantInfoStore.merchantInfo.verificationStatus
  if (state == 1) {
    verificationState.value = { text: '审核中', color: 'blue'}
  } else if (state == 0) {
    verificationState.value = { text: '未通过审核', color: 'red'}
  } else if (state == 2) {
    verificationState.value = { text: '已通过审核', color: 'green'}
  }
}

onMounted(() => {
  getCurrentMerchant().then(res => {
    if (res.data) {
      merchantInfoStore.setMerchantInfo(res.data)
      changeVerificationState()
      imageUrl1.value = merchantInfoStore.merchantInfo?.coverImage
      imageUrl2.value = merchantInfoStore.merchantInfo?.businessLicense
      imageUrl3.value = merchantInfoStore.merchantInfo?.hygienicLicense
      getCategoryName(currentCategoryId)
    } else {
      ElMessage.error("获取商家信息失败，请先登录")
      router.push({ path: '/login' })
    }
  })

})
</script>



<template>
  <div class="merchant-container">
    <div class="header-section">
      <h3 class="merchant-title">商家信息</h3>
      <el-tag
          :type="verificationState.text === '已通过审核' ? 'success' :
               verificationState.text === '审核中' ? 'warning' : 'danger'"
          class="status-tag"
      >
        {{ verificationState.text }}
      </el-tag>
    </div>

    <el-card class="merchant-card">
      <el-form label-width="120px" class="merchant-form">
        <div class="form-grid">
          <div class="form-column">
            <el-form-item label="名称" class="form-item">
              <div class="form-content">{{merchantInfoStore.merchantInfo.merchantName}}</div>
            </el-form-item>
            <el-form-item label="描述" class="form-item">
              <div class="form-content">{{merchantInfoStore.merchantInfo.description}}</div>
            </el-form-item>
            <el-form-item label="类别" class="form-item">
              <div class="form-content">{{currentCategory}}</div>
            </el-form-item>
            <el-form-item label="标签" class="form-item">
              <el-tag type="info" class="tag-item">{{merchantInfoStore.merchantInfo.tag}}</el-tag>
            </el-form-item>
            <el-form-item label="电话" class="form-item">
              <div class="form-content">
                <el-icon><iphone /></el-icon>
                {{merchantInfoStore.merchantInfo.contactPhone}}
              </div>
            </el-form-item>
            <el-form-item label="邮箱" class="form-item">
              <div class="form-content">
                <el-icon><message /></el-icon>
                {{merchantInfoStore.merchantInfo.contactEmail}}
              </div>
            </el-form-item>
          </div>

          <div class="form-column">
            <el-form-item label="地址" class="form-item">
              <div class="form-content">
                <el-icon><location /></el-icon>
                {{merchantInfoStore.merchantInfo.address}}
              </div>
            </el-form-item>
            <el-form-item label="营业时间" class="form-item">
              <div class="form-content">
                <el-icon><clock /></el-icon>
                {{merchantInfoStore.merchantInfo.businessHours}}
              </div>
            </el-form-item>
            <el-form-item label="平均价格" class="form-item">
              <div class="form-content">
                <el-icon><money /></el-icon>
                {{merchantInfoStore.merchantInfo.priceLevel}}
              </div>
            </el-form-item>
            <el-form-item label="审核信息" class="form-item" v-if="merchantInfoStore.merchantInfo.review">
              <div class="form-content review-message">
                <el-icon><info-filled /></el-icon>
                {{merchantInfoStore.merchantInfo.review}}
              </div>
            </el-form-item>
          </div>
        </div>

        <div class="image-section">
          <el-form-item label="封面图片" class="image-item">
            <el-image
                v-if="imageUrl1"
                :src="imageUrl1"
                class="merchant-image"
                :preview-src-list="[imageUrl1]"
                fit="cover"
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Postcard /></el-icon>
                  <span>图片加载失败</span>
                </div>
              </template>
            </el-image>
            <div v-else class="image-placeholder">
              <el-icon><Postcard /></el-icon>
              <span>暂无封面图片</span>
            </div>
          </el-form-item>

          <el-form-item label="营业执照" class="image-item">
            <el-image
                v-if="imageUrl2"
                :src="imageUrl2"
                class="merchant-image"
                :preview-src-list="[imageUrl2]"
                fit="cover"
            >
              <template #error>
                <div class="image-error">
                  <el-icon><document /></el-icon>
                  <span>图片加载失败</span>
                </div>
              </template>
            </el-image>
            <div v-else class="image-placeholder">
              <el-icon><document /></el-icon>
              <span>暂无营业执照</span>
            </div>
          </el-form-item>

          <el-form-item label="卫生许可证" class="image-item">
            <el-image
                v-if="imageUrl3"
                :src="imageUrl3"
                class="merchant-image"
                :preview-src-list="[imageUrl3]"
                fit="cover"
            >
              <template #error>
                <div class="image-error">
                  <el-icon><tickets /></el-icon>
                  <span>图片加载失败</span>
                </div>
              </template>
            </el-image>
            <div v-else class="image-placeholder">
              <el-icon><tickets /></el-icon>
              <span>暂无卫生许可证</span>
            </div>
          </el-form-item>
        </div>
      </el-form>

      <div class="action-buttons">
        <el-button
            type="primary"
            @click="showEditDialog()"
            class="edit-button"
        >
          <el-icon><edit /></el-icon>
          修改信息
        </el-button>
      </div>
    </el-card>

    <el-dialog
        v-model="isShow"
        title="修改商家信息"
        width="700px"
        class="edit-dialog"
    >
      <span>
       <el-form :model="merchant" label-width="auto" style="max-width: 600px">
          <el-form-item label="名称">
            <el-input v-model="merchant.merchantName" placeholder="请输入名称"/>
          </el-form-item>
          <el-form-item label="密码">
            <i class="el-icon-lock"></i>
            <el-input v-model="merchant.merchantPassword" placeholder="请输入密码" type="password" show-password></el-input>
          </el-form-item>
          <el-form-item label="确认密码">
            <i class="el-icon-lock"></i>
            <el-input v-model="password" placeholder="请再次确认密码" type="password" show-password @change="checkPassword"></el-input>
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="merchant.description" placeholder="请输入描述"/>
          </el-form-item>
          <el-form-item label="类别">
            <el-select v-model="parentId" placeholder="请选择商家类别" clearable @change="getParentList()">
              <el-option v-for="(item, index) in parentList" :key="index" :label="item.parentName" :value="item.parentId" />
            </el-select>
            <el-select v-model="childrenId" placeholder="请选择商家子类别" clearable style="margin-top: 18px;" @change="getChildrenList()">
              <el-option v-for="(item, index) in childrenList" :key="index" :label="item.childrenName" :value="item.childrenId" />
            </el-select>
            <el-select v-model="grandId" placeholder="请选择商家子子类别" clearable style="margin-top: 18px;">
              <el-option v-for="(item, index) in grandList" :key="index" :label="item.grandName" :value="item.grandId" />
            </el-select>
          </el-form-item>
          <el-form-item label="标签">
            <el-input v-model="merchant.tag" placeholder="请输入标签"/>
          </el-form-item>
          <el-form-item label="电话">
            <el-input v-model="merchant.contactPhone" placeholder="请输入电话"/>
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="merchant.contactEmail" placeholder="请输入邮箱"/>
          </el-form-item>
          <el-form-item label="地址">
            <el-input v-model="merchant.address" placeholder="请输入地址"/>
          </el-form-item>
          <el-form-item label="封面">
            <el-upload
                class="avatar-uploader"
                action="/api/file/upload"
                :show-file-list="false"
                :on-success="handleCoverImageSuccess"
            >
              <img v-if="imageUrl1" :src="imageUrl1" class="avatar" style="height: 150px"/>
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
          </el-form-item>
          <el-form-item label="营业执照">
            <el-upload
                class="avatar-uploader"
                action="/api/file/upload"
                :show-file-list="false"
                :on-success="handleBusinessLicenseSuccess"
            >
              <img v-if="imageUrl2" :src="imageUrl2" class="avatar" style="height: 150px"/>
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
          </el-form-item>
          <el-form-item label="卫生许可证">
            <el-upload
                class="avatar-uploader"
                action="/api/file/upload"
                :show-file-list="false"
                :on-success="handleHygienicLicenseSuccess"
            >
              <img v-if="imageUrl3" :src="imageUrl3" class="avatar" style="height: 150px"/>
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
          </el-form-item>
          <el-form-item label="营业时间">
            <el-col :span="11">
              <el-time-picker
                  v-model="startTime"
                  placeholder="开始营业"
                  style="width: 100%"
                  value-format="HH:mm:ss"
                  @change="getBusinessHours"
              />
            </el-col>
            <el-col :span="2" class="text-center">
              <span class="text-gray-500">-</span>
            </el-col>
            <el-col :span="11">
              <el-time-picker
                  v-model="endTime"
                  placeholder="结束营业"
                  style="width: 100%"
                  value-format="HH:mm:ss"
                  @change="getBusinessHours"
              />
            </el-col>
          </el-form-item>
          <el-form-item label="平均价格">
            <el-input v-model="merchant.priceLevel" placeholder="请输入平均价格"/>
          </el-form-item>
        </el-form>
      </span>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="isShow = false">取消</el-button>
          <el-button type="primary" @click="changeMerchant">
            修改
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.merchant-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

.header-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.merchant-title {
  color: #303133;
  font-size: 24px;
  margin: 0;
}

.status-tag {
  font-size: 14px;
  padding: 8px 15px;
}

.merchant-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
}

.merchant-form {
  padding: 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-column {
  display: flex;
  flex-direction: column;
}

.form-item {
  margin-bottom: 18px;
}

.form-content {
  padding: 8px 0;
  color: #606266;
  min-height: 20px;
  line-height: 1.5;
}

.tag-item {
  margin-right: 8px;
}

.image-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 20px;
  padding-right: 60px;
}

.image-item {
  margin-bottom: 0;
}

.merchant-image {
  width: 100%;
  height: 200px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  overflow: hidden;
}

.image-placeholder,
.image-error {
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  background-color: #f5f7fa;
  border-radius: 4px;
  border: 1px dashed #dcdfe6;
}

.image-placeholder .el-icon,
.image-error .el-icon {
  font-size: 40px;
  margin-bottom: 10px;
  color: #c0c4cc;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.edit-button {
  padding: 10px 20px;
}

.review-message {
  color: #ff9b25;
  background-color: #fef0f0;
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 4px solid #f5de6c;
}

@media (max-width: 992px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .image-section {
    grid-template-columns: 1fr;
  }
}

.edit-dialog {
  border-radius: 8px;
}

.edit-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #ebeef5;
  margin-right: 0;
}

.edit-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.edit-dialog :deep(.el-dialog__footer) {
  border-top: 1px solid #ebeef5;
  padding: 15px 20px;
}

.merchant-container {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(190, 214, 205, 0.78);
  box-shadow: 0 18px 44px rgba(22, 53, 45, 0.08);
}

.header-section,
.form-column,
.image-section,
.status-info {
  border-radius: 18px;
  border-color: rgba(190, 214, 205, 0.72);
  box-shadow: none;
}

.header-section {
  padding: 18px 22px;
  gap: 14px;
}

.merchant-title {
  margin: 0;
}

.status-tag {
  margin-right: 2px;
}

.merchant-container :deep(.el-button) {
  border-radius: 999px;
  box-shadow: none !important;
}

.merchant-container :deep(.el-button--primary) {
  background: #2f7d6b;
  border-color: #2f7d6b;
}
</style>
