<script setup lang="ts">
import {reactive, ref} from 'vue';
import {merchantRegister1, getParentList1} from "@/api/merchant";

const merchant = reactive({
  merchantName: '',
  description: '',
  categoryId: '',
  tag: '',
  contactPhone: '',
  contactEmail: '',
  address: '',
  coverImage: '',
  businessLicense: '',
  hygienicLicense: '',
  businessHours: '',
  priceLevel: '',
  merchantPassword: '',
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

import { Plus } from '@element-plus/icons-vue'
import {ElMessage} from "element-plus";
import {useRouter} from "vue-router";
const imageUrl1 = ref('')
const imageUrl2 = ref('')
const imageUrl3 = ref('')
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
const router = useRouter()
const merchantRegister = () => {
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
  merchantRegister1(merchant).then(res => {
    ElMessage({
      message: '注册成功',
      type: 'success',
    })
    router.push({path: '/login'})
  })
}
const password = ref('')
function checkPassword() {
  if (merchant.merchantPassword !== password.value) {
    ElMessage({
      message: '两次输入的密码不一致',
      type: 'error',
    })
  }
}
const gotoLogin = () => {
  router.push({path: '/login'})
}
</script>
<template>
  <div class="regist-container">
    <h3>商家注册</h3>
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
            <div class="dialog-footer">
              <el-button type="primary" @click="merchantRegister">
                注册
              </el-button>
              <el-button type="" @click="gotoLogin">
                已有账号？去登录
              </el-button>
            </div>
        </el-form>
  </div>
</template>

<style lang="scss" scoped>
.regist-container {
  width: 600px;
  margin: 0 auto;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.avatar-uploader .avatar {
  width: 178px;
  height: 178px;
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
  width: 178px;
  height: 178px;
  text-align: center;
}
</style>
