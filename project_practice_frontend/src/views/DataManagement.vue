<template>
  <div class="data-management-container">
    <el-card class="data-card">
      <template #header>
        <div class="card-header">
          <span>数据集管理</span>
          <el-button type="primary" @click="showUploadDialog">上传数据集</el-button>
        </div>
      </template>
      
      <!-- 数据集筛选 -->
      <div class="filter-container">
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="数据类型">
            <el-select v-model="filterForm.category" placeholder="全部类型" clearable>
              <el-option label="电力数据" value="power" />
              <el-option label="交通数据" value="traffic" />
              <el-option label="气候数据" value="climate" />
              <el-option label="自定义数据" value="custom" />
            </el-select>
          </el-form-item>
          <el-form-item label="数据来源">
            <el-select v-model="filterForm.isPreset" placeholder="全部来源" clearable>
              <el-option label="系统预设" :value="true" />
              <el-option label="用户上传" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleFilter">筛选</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 数据集列表 -->
      <el-table
        v-loading="loading"
        :data="datasetList"
        style="width: 100%"
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="数据集名称" min-width="180" />
        <el-table-column prop="category" label="类型" width="120">
          <template #default="scope">
            <el-tag :type="getCategoryTagType(scope.row.category)">
              {{ getCategoryLabel(scope.row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rows" label="数据量" width="120" />
        <el-table-column prop="timeRange" label="时间范围" min-width="180" />
        <el-table-column prop="isPreset" label="来源" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.isPreset ? 'info' : 'success'">
              {{ scope.row.isPreset ? '系统预设' : '用户上传' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button type="text" size="small" @click="viewDataset(scope.row)">查看</el-button>
            <el-button type="text" size="small" @click="previewDataset(scope.row)">预览</el-button>
            <el-button 
              type="text" 
              size="small" 
              @click="downloadDataset(scope.row)"
              :disabled="!scope.row.downloadable"
            >下载</el-button>
            <el-button 
              type="text" 
              size="small" 
              @click="deleteDataset(scope.row)"
              :disabled="scope.row.isPreset"
              class="delete-btn"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 上传数据集对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传数据集"
      width="500px"
    >
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
        <el-form-item label="数据集名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入数据集名称" />
        </el-form-item>
        <el-form-item label="数据类型" prop="category">
          <el-select v-model="uploadForm.category" placeholder="请选择数据类型" style="width: 100%">
            <el-option label="电力数据" value="power" />
            <el-option label="交通数据" value="traffic" />
            <el-option label="气候数据" value="climate" />
            <el-option label="自定义数据" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="uploadForm.description" type="textarea" rows="3" placeholder="请输入数据集描述" />
        </el-form-item>
        <el-form-item label="上传文件" prop="file">
          <el-upload
            class="upload-demo"
            action="#"
            :auto-upload="false"
            :on-change="handleUploadChange"
            :limit="1"
            :file-list="uploadFileList"
          >
            <template #trigger>
              <el-button type="primary">选择文件</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                请上传CSV格式的时间序列数据，文件大小不超过50MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 数据集预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="数据集预览"
      width="80%"
    >
      <div v-loading="previewLoading" class="preview-container">
        <div class="preview-header">
          <h3>{{ currentDataset.name }}</h3>
          <p>{{ currentDataset.description }}</p>
        </div>
        
        <el-divider />
        
        <div class="preview-table-container">
          <el-table
            :data="previewData.rows"
            style="width: 100%"
            border
            max-height="400px"
          >
            <el-table-column
              v-for="column in previewData.columns"
              :key="column"
              :prop="column"
              :label="column"
              min-width="120"
            />
          </el-table>
        </div>
        
        <el-divider />
        
        <div class="preview-stats">
          <el-descriptions title="数据集统计信息" :column="3" border>
            <el-descriptions-item label="总行数">{{ previewData.stats.rowCount }}</el-descriptions-item>
            <el-descriptions-item label="总列数">{{ previewData.stats.columnCount }}</el-descriptions-item>
            <el-descriptions-item label="时间范围">{{ previewData.stats.timeRange }}</el-descriptions-item>
            <el-descriptions-item label="缺失值">{{ previewData.stats.missingValues }}</el-descriptions-item>
            <el-descriptions-item label="数值列">{{ previewData.stats.numericColumns }}</el-descriptions-item>
            <el-descriptions-item label="分类列">{{ previewData.stats.categoricalColumns }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { datasetAPI } from '@/api'

// 状态变量
const loading = ref(false)
const uploading = ref(false)
const previewLoading = ref(false)
const uploadDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const uploadFileList = ref([])
const datasetList = ref([])
const uploadFormRef = ref(null)

// 当前选中的数据集
const currentDataset = ref({})

// 筛选表单
const filterForm = reactive({
  category: '',
  isPreset: ''
})

// 上传表单
const uploadForm = reactive({
  name: '',
  category: 'custom',
  description: '',
  file: null
})

// 上传表单验证规则
const uploadRules = {
  name: [
    { required: true, message: '请输入数据集名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度应为2-50个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择数据类型', trigger: 'change' }
  ],
  file: [
    { required: true, message: '请上传数据文件', trigger: 'change' }
  ]
}

// 分页信息
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 预览数据
const previewData = reactive({
  columns: [],
  rows: [],
  stats: {
    rowCount: 0,
    columnCount: 0,
    timeRange: '',
    missingValues: 0,
    numericColumns: 0,
    categoricalColumns: 0
  }
})

// 获取数据集列表
const fetchDatasets = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      per_page: pagination.pageSize,
      ...filterForm
    }
    
    const response = await datasetAPI.getDatasets(params)
    if (response.success) {
      datasetList.value = response.data.map(item => ({
        ...item,
        downloadable: !item.isPreset || item.allowDownload,
        createdAt: formatDate(item.createdAt)
      }))
      pagination.total = response.total
    } else {
      ElMessage.error(response.message || '获取数据集列表失败')
    }
  } catch (error) {
    console.error('获取数据集列表出错:', error)
    ElMessage.error('获取数据集列表失败')
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取类型标签样式
const getCategoryTagType = (category) => {
  const types = {
    power: 'danger',
    traffic: 'warning',
    climate: 'success',
    custom: 'info'
  }
  return types[category] || 'info'
}

// 获取类型标签文本
const getCategoryLabel = (category) => {
  const labels = {
    power: '电力数据',
    traffic: '交通数据',
    climate: '气候数据',
    custom: '自定义数据'
  }
  return labels[category] || '未知类型'
}

// 处理筛选
const handleFilter = () => {
  pagination.currentPage = 1
  fetchDatasets()
}

// 重置筛选
const resetFilter = () => {
  filterForm.category = ''
  filterForm.isPreset = ''
  handleFilter()
}

// 处理分页大小变化
const handleSizeChange = (size) => {
  pagination.pageSize = size
  fetchDatasets()
}

// 处理页码变化
const handleCurrentChange = (page) => {
  pagination.currentPage = page
  fetchDatasets()
}

// 显示上传对话框
const showUploadDialog = () => {
  uploadForm.name = ''
  uploadForm.category = 'custom'
  uploadForm.description = ''
  uploadForm.file = null
  uploadFileList.value = []
  uploadDialogVisible.value = true
}

// 处理文件上传变化
const handleUploadChange = (file) => {
  uploadForm.file = file.raw
  
  // 验证文件类型
  const isCSV = file.raw.type === 'text/csv' || file.name.endsWith('.csv')
  if (!isCSV) {
    ElMessage.error('请上传CSV格式的文件')
    uploadFileList.value = []
    return false
  }
  
  // 验证文件大小
  const isLt50M = file.raw.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过50MB')
    uploadFileList.value = []
    return false
  }
}

// 提交上传
const submitUpload = async () => {
  if (!uploadForm.file) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }
  
  uploadFormRef.value.validate(async (valid) => {
    if (valid) {
      uploading.value = true
      try {
        const formData = new FormData()
        formData.append('name', uploadForm.name)
        formData.append('category', uploadForm.category)
        formData.append('description', uploadForm.description)
        formData.append('file', uploadForm.file)
        
        const response = await datasetAPI.uploadDataset(formData)
        if (response.success) {
          ElMessage.success('数据集上传成功')
          uploadDialogVisible.value = false
          fetchDatasets()
        } else {
          ElMessage.error(response.message || '上传失败')
        }
      } catch (error) {
        console.error('上传数据集出错:', error)
        ElMessage.error('上传数据集失败')
      } finally {
        uploading.value = false
      }
    }
  })
}

// 查看数据集
const viewDataset = (dataset) => {
  // 实现查看数据集详情的逻辑
  ElMessage.info('查看数据集: ' + dataset.name)
}

// 预览数据集
const previewDataset = async (dataset) => {
  currentDataset.value = dataset
  previewDialogVisible.value = true
  previewLoading.value = true
  
  try {
    const response = await datasetAPI.previewDataset(dataset.id)
    if (response.success) {
      previewData.columns = response.data.columns
      previewData.rows = response.data.rows
      previewData.stats = response.data.stats
    } else {
      ElMessage.error(response.message || '获取数据集预览失败')
    }
  } catch (error) {
    console.error('预览数据集出错:', error)
    ElMessage.error('预览数据集失败')
  } finally {
    previewLoading.value = false
  }
}

// 下载数据集
const downloadDataset = async (dataset) => {
  try {
    const response = await datasetAPI.downloadDataset(dataset.id)
    if (response.success) {
      // 处理文件下载
      const url = response.data.downloadUrl
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${dataset.name}.csv`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } else {
      ElMessage.error(response.message || '下载数据集失败')
    }
  } catch (error) {
    console.error('下载数据集出错:', error)
    ElMessage.error('下载数据集失败')
  }
}

// 删除数据集
const deleteDataset = (dataset) => {
  ElMessageBox.confirm(
    `确定要删除数据集 "${dataset.name}" 吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const response = await datasetAPI.deleteDataset(dataset.id)
      if (response.success) {
        ElMessage.success('数据集删除成功')
        fetchDatasets()
      } else {
        ElMessage.error(response.message || '删除数据集失败')
      }
    } catch (error) {
      console.error('删除数据集出错:', error)
      ElMessage.error('删除数据集失败')
    }
  }).catch(() => {
    // 取消删除
  })
}

// 页面加载时获取数据集列表
onMounted(() => {
  fetchDatasets()
})
</script>

<style scoped>
.data-management-container {
  padding: 20px;
}

.data-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-container {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.preview-container {
  min-height: 400px;
}

.preview-header {
  margin-bottom: 20px;
}

.preview-table-container {
  margin-bottom: 20px;
}

.preview-stats {
  margin-top: 20px;
}

.delete-btn {
  color: #f56c6c;
}
</style>