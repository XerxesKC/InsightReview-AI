<template>
  <div class="kb-management page-shell">
    <el-card shadow="never" class="shell-card shell-card--filters">
      <template #header>
        <div class="shell-card__header">
          <div>
            <span class="shell-card__eyebrow">知识库筛选</span>
            <h2 class="shell-card__title">知识库管理</h2>
          </div>
          <span class="shell-card__badge">按名称、归属角色与时间检索</span>
        </div>
      </template>

      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="名称">
          <el-input v-model="filters.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="归属角色">
          <el-select v-model="filters.owner_type" placeholder="请选择角色">
            <el-option label="全部" value="" />
            <el-option label="商家" value="merchant" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="filters.created_from" type="datetime" placeholder="开始时间" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="filters.created_to" type="datetime" placeholder="结束时间" />
        </el-form-item>
      </el-form>

      <div class="toolbar">
        <div class="toolbar__left">
          <button class="action-pill action-pill--primary" type="button" @click="loadKnowledgeBases">查询</button>
          <button class="action-pill" type="button" @click="resetFilters">重置</button>
        </div>
        <button class="action-pill action-pill--primary" type="button" @click="openCreateDialog">新建知识库</button>
      </div>
    </el-card>

    <el-card shadow="never" class="shell-card shell-card--table">
      <template #header>
        <div class="shell-card__header shell-card__header--wide">
          <div>
            <span class="shell-card__eyebrow">知识库列表</span>
            <h2 class="shell-card__title">当前知识库</h2>
            <p class="shell-card__hint">统一查看知识库描述、归属人、模型与向量库关联状态。</p>
          </div>
          <span class="shell-card__badge">可直接编辑与删除</span>
        </div>
      </template>

      <div class="table-stage">
        <el-table :data="knowledgeBases" class="knowledge-table">
          <el-table-column prop="name" label="名称" width="200" />
          <el-table-column prop="description" label="描述" min-width="220" />
          <el-table-column prop="department" label="归属角色" width="120" />
          <el-table-column prop="owner" label="归属人" width="140" />
          <el-table-column label="Embedding 模型" width="170">
            <template #default="scope">
              {{ scope.row.embedding_model }}
            </template>
          </el-table-column>
          <el-table-column label="向量库" min-width="180">
            <template #default="scope">
              {{ scope.row.chroma_collection || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="scope">
              <el-button size="small" @click="editKnowledgeBase(scope.row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteKnowledgeBase(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <el-dialog :title="dialogTitle" v-model="showCreateDialog" width="680px" class="dialog-shell">
      <el-form ref="formRef" :model="form" label-width="100px" :rules="rules" class="dialog-form">
        <el-form-item label="知识库名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="归属角色" prop="owner_type">
          <el-select v-model="form.owner_type" placeholder="请选择" @change="handleOwnerTypeChange">
            <el-option label="商家" value="merchant" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="归属人" prop="owner_id">
          <el-select
            v-model="form.owner_id"
            placeholder="请先选择归属角色"
            :disabled="!form.owner_type"
            filterable
            :filter-method="filterOwners"
            @focus="loadOwners"
          >
            <el-option
              v-for="owner in owners"
              :key="owner.id"
              :label="owner.name"
              :value="owner.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Embedding 模型" prop="embedding_model">
          <el-select v-model="form.embedding_model" placeholder="请选择">
            <el-option
              v-for="model in embeddingModels"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="向量库" prop="chroma_collection">
          <div v-if="!form.owner_type || !form.owner_id" class="state-block state-block--info">
            请先选择归属角色和归属人
            <input type="hidden" v-model="form.chroma_collection" value="" />
          </div>
          <div v-else-if="matchingCollection" class="state-block state-block--success">
            {{ matchingCollection }}
            <input type="hidden" v-model="form.chroma_collection" />
          </div>
          <div v-else class="state-block state-block--warn">
            暂无对应向量库
            <input type="hidden" v-model="form.chroma_collection" value="" />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="submit">{{ isEditing ? "更新" : "创建" }}</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import {
  createKnowledgeBase,
  getKnowledgeBases,
  updateKnowledgeBase,
  deleteKnowledgeBase as removeKnowledgeBase,
  getEmbeddingModels,
  getVectorCollections,
  getOwners,
} from "@/api/knowledgeBase";
import { ElMessage, ElMessageBox } from "element-plus";

export default {
  data() {
    return {
      knowledgeBases: [],
      showCreateDialog: false,
      isEditing: false,
      editingId: null,
      form: {
        admin_id: "1",
        name: "",
        description: "",
        owner_type: "",
        owner_id: "",
        embedding_model: "",
        chroma_collection: "",
      },
      filters: {
        name: "",
        owner_type: "",
        created_from: "",
        created_to: "",
      },
      embeddingModels: [],
      matchingCollection: null,
      owners: [],
      ownerKeyword: "",
      rules: {
        name: [{ required: true, message: "请输入知识库名称", trigger: "blur" }],
        description: [{ required: true, message: "请输入描述", trigger: "blur" }],
        owner_type: [{ required: true, message: "请选择归属角色", trigger: "change" }],
        owner_id: [{ required: true, message: "请选择归属人", trigger: "change" }],
        embedding_model: [{ required: true, message: "请选择 Embedding 模型", trigger: "change" }],
        chroma_collection: [{ required: true, message: "请确认向量库关联状态", trigger: "blur" }],
      },
    };
  },
  computed: {
    dialogTitle() {
      return this.isEditing ? "编辑知识库" : "创建知识库";
    },
  },
  mounted() {
    this.loadKnowledgeBases();
  },
  watch: {
    showCreateDialog(val) {
      if (val) {
        this.loadKbOptions();
      } else {
        this.resetForm();
      }
    },
    "form.owner_id": {
      handler() {
        this.loadVectorCollections();
      },
      immediate: false,
    },
  },
  methods: {
    async loadKbOptions() {
      try {
        await this.loadEmbeddingModels();
        await this.loadVectorCollections();
      } catch (e) {
        ElMessage.error("知识库选项加载失败");
      }
    },
    async loadEmbeddingModels() {
      try {
        const res = await getEmbeddingModels();
        this.embeddingModels = res.data || [];
      } catch (e) {
        this.embeddingModels = [];
        ElMessage.error("模型列表加载失败");
      }
    },
    async loadVectorCollections() {
      try {
        const res = await getVectorCollections(this.form.owner_type, this.form.owner_id);
        const collections = res.data || [];
        if (this.form.owner_type && this.form.owner_id) {
          const targetCollection = `${this.form.owner_type}_${this.form.owner_id}`;
          this.matchingCollection = collections.find((col) => col === targetCollection) || null;
        } else {
          this.matchingCollection = null;
        }
        this.form.chroma_collection = this.matchingCollection || "";
      } catch (e) {
        this.matchingCollection = null;
        this.form.chroma_collection = "";
        ElMessage.error("向量库列表加载失败");
      }
    },
    async loadKnowledgeBases() {
      try {
        const params = {};
        if (this.filters.name) params.name = this.filters.name;
        if (this.filters.owner_type) params.owner_type = this.filters.owner_type;
        if (this.filters.created_from) {
          params.created_from = new Date(this.filters.created_from).toISOString().slice(0, 19).replace("T", " ");
        }
        if (this.filters.created_to) {
          params.created_to = new Date(this.filters.created_to).toISOString().slice(0, 19).replace("T", " ");
        }
        const res = await getKnowledgeBases(params);
        const departmentMap = { merchant: "商家", admin: "管理员" };
        this.knowledgeBases = (res.data || []).map((kb) => ({
          ...kb,
          department: departmentMap[kb.owner_type] || kb.owner_type,
          owner: kb.owner_name || `未知归属人(${kb.owner_id})`,
        }));
      } catch (e) {
        ElMessage.error("知识库列表加载失败");
      }
    },
    resetFilters() {
      this.filters = {
        name: "",
        owner_type: "",
        created_from: "",
        created_to: "",
      };
      this.loadKnowledgeBases();
    },
    async handleOwnerTypeChange() {
      this.form.owner_id = "";
      this.owners = [];
      this.ownerKeyword = "";
      if (this.form.owner_type) {
        await this.loadOwners();
      }
      await this.loadVectorCollections();
    },
    async loadOwners() {
      if (!this.form.owner_type) return;
      try {
        const res = await getOwners(this.form.owner_type, this.ownerKeyword);
        this.owners = res.data || [];
      } catch (e) {
        this.owners = [];
        ElMessage.error("归属人列表加载失败");
      }
    },
    filterOwners(query) {
      this.ownerKeyword = query;
      this.loadOwners();
    },
    formatDateTime(value) {
      if (!value) return "-";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return String(value);
      const yyyy = date.getFullYear();
      const mm = String(date.getMonth() + 1).padStart(2, "0");
      const dd = String(date.getDate()).padStart(2, "0");
      const hh = String(date.getHours()).padStart(2, "0");
      const mi = String(date.getMinutes()).padStart(2, "0");
      const ss = String(date.getSeconds()).padStart(2, "0");
      return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`;
    },
    openCreateDialog() {
      this.isEditing = false;
      this.editingId = null;
      this.resetForm();
      this.showCreateDialog = true;
    },
    async editKnowledgeBase(kb) {
      this.isEditing = true;
      this.editingId = kb.id;
      this.form = {
        ...kb,
        owner_id: kb.owner_id ? String(kb.owner_id) : "",
      };
      if (this.form.owner_type) {
        await this.loadOwners();
      }
      this.showCreateDialog = true;
    },
    async deleteKnowledgeBase(id) {
      try {
        await ElMessageBox.confirm("确定删除这个知识库吗？", "提示", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        });
        await removeKnowledgeBase(id);
        ElMessage.success("删除成功");
        this.loadKnowledgeBases();
      } catch (e) {
        if (e !== "cancel") {
          ElMessage.error("删除失败");
        }
      }
    },
    async submit() {
      try {
        await this.$refs.formRef.validate();
        if (this.isEditing) {
          await updateKnowledgeBase(this.editingId, this.form);
          ElMessage.success("更新成功");
        } else {
          await createKnowledgeBase(this.form);
          ElMessage.success("创建成功");
        }
        this.showCreateDialog = false;
        this.resetForm();
        this.loadKnowledgeBases();
      } catch (e) {
        if (e !== "cancel") {
          ElMessage.error(this.isEditing ? "更新失败" : "创建失败");
        }
      }
    },
    resetForm() {
      this.form = {
        admin_id: "1",
        name: "",
        description: "",
        owner_type: "",
        owner_id: "",
        embedding_model: "",
        chroma_collection: "",
      };
      this.isEditing = false;
      this.editingId = null;
      this.owners = [];
      this.ownerKeyword = "";
      this.matchingCollection = null;
    },
  },
};
</script>

<style scoped>
.page-shell {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.shell-card {
  border-radius: 28px;
  overflow: hidden;
}

.shell-card :deep(.el-card__body) {
  padding: 24px;
}

.shell-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.shell-card__header--wide {
  align-items: flex-start;
}

.shell-card__eyebrow {
  display: inline-flex;
  color: var(--rv-text-faint);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.shell-card__title {
  margin: 8px 0 0;
  color: var(--rv-text);
  font-size: 28px;
  line-height: 1.08;
}

.shell-card__hint {
  margin: 10px 0 0;
  color: var(--rv-text-soft);
  line-height: 1.7;
}

.shell-card__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(49, 94, 251, 0.08);
  color: var(--rv-primary);
  font-size: 12px;
  font-weight: 700;
}

.shell-card--filters,
.shell-card--table {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 253, 0.97));
}

.filter-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 18px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

.filter-form :deep(.el-input),
.filter-form :deep(.el-select),
.filter-form :deep(.el-date-editor) {
  width: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 12px;
}

.toolbar__left {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-pill {
  appearance: none;
  border: 1px solid rgba(76, 93, 128, 0.12);
  background: rgba(255, 255, 255, 0.92);
  color: var(--rv-text);
  border-radius: 999px;
  padding: 12px 18px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.action-pill--primary {
  border-color: transparent;
  background: linear-gradient(135deg, #3667ff 0%, #5f86ff 100%);
  color: #ffffff;
  box-shadow: 0 16px 28px rgba(54, 103, 255, 0.2);
}

.table-stage {
  padding: 14px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(247, 249, 252, 0.92), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(72, 88, 117, 0.08);
}

.dialog-form :deep(.el-select),
.dialog-form :deep(.el-input),
.dialog-form :deep(.el-textarea) {
  width: 100%;
}

.state-block {
  width: 100%;
  padding: 12px 14px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.6;
}

.state-block--info {
  background: rgba(49, 94, 251, 0.08);
  color: var(--rv-primary);
}

.state-block--success {
  background: rgba(15, 118, 110, 0.08);
  color: #0f766e;
}

.state-block--warn {
  background: rgba(148, 163, 184, 0.12);
  color: var(--rv-text-soft);
}

@media (max-width: 960px) {
  .filter-form {
    grid-template-columns: 1fr;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
