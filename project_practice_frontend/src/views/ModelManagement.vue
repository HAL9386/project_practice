<template>
  <div class="model-management-container">
    <el-card class="model-card">
      <template #header>
        <div class="card-header">
          <span>预测模型管理</span>
        </div>
      </template>
      
      <!-- 模型筛选 -->
      <div class="filter-container">
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="模型类型">
            <el-select v-model="filterForm.type" placeholder="全部类型" clearable>
              <el-option label="CrossGNN" value="CrossGNN" />
              <el-option label="HDMixer" value="HDMixer" />
              <el-option label="LeRet" value="LeRet" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleFilter">筛选</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 模型列表 -->
      <el-table
        v-loading="loading"
        :data="modelList"
        style="width: 100%"
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="模型名称" min-width="180" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="scope">
            <el-tag :type="getModelTagType(scope.row.type)">
              {{ scope.row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="parameters" label="参数数量" width="120" />
        <el-table-column prop="accuracy" label="准确率" width="120">
          <template #default="scope">
            {{ scope.row.accuracy }}%
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button type="text" size="small" @click="viewModelDetails(scope.row)">详情</el-button>
            <el-button type="text" size="small" @click="configureModel(scope.row)">配置</el-button>
            <el-button type="text" size="small" @click="viewModelPerformance(scope.row)">性能</el-button>
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
    
    <!-- 模型详情对话框 -->
    <el-dialog
      v-model="detailsDialogVisible"
      title="模型详情"
      width="60%"
    >
      <div v-loading="detailsLoading" class="model-details-container">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模型名称">{{ currentModel.name }}</el-descriptions-item>
          <el-descriptions-item label="模型类型">{{ currentModel.type }}</el-descriptions-item>
          <el-descriptions-item label="参数数量">{{ currentModel.parameters }}</el-descriptions-item>
          <el-descriptions-item label="准确率">{{ currentModel.accuracy }}%</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentModel.createdAt }}</el-descriptions-item>
          <el-descriptions-item label="最后更新">{{ currentModel.updatedAt }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentModel.description }}</el-descriptions-item>
        </el-descriptions>
        
        <el-divider content-position="left">模型架构</el-divider>
        
        <div class="model-architecture">
          <pre>{{ currentModel.architecture }}</pre>
        </div>
        
        <el-divider content-position="left">默认超参数</el-divider>
        
        <el-table :data="hyperParamsData" border style="width: 100%">
          <el-table-column prop="name" label="参数名称" width="180" />
          <el-table-column prop="value" label="默认值" width="120" />
          <el-table-column prop="description" label="说明" min-width="200" />
          <el-table-column prop="range" label="取值范围" width="180" />
        </el-table>
      </div>
    </el-dialog>
    
    <!-- 模型配置对话框 -->
    <el-dialog
      v-model="configDialogVisible"
      title="模型配置"
      width="50%"
    >
      <el-form :model="configForm" label-width="120px">
        <el-form-item v-for="(param, index) in configParams" :key="index" :label="param.name">
          <el-tooltip :content="param.description" placement="top">
            <template v-if="param.type === 'number'">
              <el-input-number 
                v-model="configForm[param.key]" 
                :min="param.min" 
                :max="param.max" 
                :step="param.step"
              />
            </template>
            <template v-else-if="param.type === 'select'">
              <el-select v-model="configForm[param.key]" style="width: 100%">
                <el-option 
                  v-for="option in param.options" 
                  :key="option.value" 
                  :label="option.label" 
                  :value="option.value"
                />
              </el-select>
            </template>
            <template v-else-if="param.type === 'switch'">
              <el-switch v-model="configForm[param.key]" />
            </template>
            <template v-else>
              <el-input v-model="configForm[param.key]" />
            </template>
          </el-tooltip>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="configDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveModelConfig">保存配置</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 模型性能对话框 -->
    <el-dialog
      v-model="performanceDialogVisible"
      title="模型性能"
      width="80%"
    >
      <div v-loading="performanceLoading" class="performance-container">
        <div class="performance-header">
          <h3>{{ currentModel.name }} 性能指标</h3>
        </div>
        
        <el-divider />
        
        <!-- 性能指标卡片 -->
        <el-row :gutter="20" class="metrics-cards">
          <el-col :span="6" v-for="(metric, index) in performanceMetrics" :key="index">
            <el-card shadow="hover" class="metric-card">
              <div class="metric-value">{{ metric.value }}</div>
              <div class="metric-name">{{ metric.name }}</div>
            </el-card>
          </el-col>
        </el-row>
        
        <el-divider />
        
        <!-- 性能图表 -->
        <div class="chart-container" ref="performanceChartRef"></div>
        
        <el-divider />
        
        <!-- 数据集性能对比 -->
        <div class="dataset-comparison">
          <h4>不同数据集上的性能</h4>
          <el-table :data="datasetPerformance" border style="width: 100%">
            <el-table-column prop="dataset" label="数据集" min-width="180" />
            <el-table-column prop="mse" label="MSE" width="120" />
            <el-table-column prop="mae" label="MAE" width="120" />
            <el-table-column prop="rmse" label="RMSE" width="120" />
            <el-table-column prop="accuracy" label="准确率" width="120">
              <template #default="scope">
                <el-progress :percentage="scope.row.accuracy" :format="format => `${format}%`" />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { modelAPI } from '@/api'
import * as echarts from 'echarts'

// 状态变量
const loading = ref(false)
const detailsLoading = ref(false)
const performanceLoading = ref(false)
const detailsDialogVisible = ref(false)
const configDialogVisible = ref(false)
const performanceDialogVisible = ref(false)
const modelList = ref([])
const performanceChartRef = ref(null)
let performanceChart = null

// 当前选中的模型
const currentModel = ref({})

// 筛选表单
const filterForm = reactive({
  type: ''
})

// 配置表单
const configForm = reactive({})
const configParams = ref([])

// 分页信息
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 超参数数据
const hyperParamsData = ref([])

// 性能指标
const performanceMetrics = ref([
  { name: 'MSE', value: '0.0234' },
  { name: 'MAE', value: '0.0156' },
  { name: 'RMSE', value: '0.1531' },
  { name: 'R²', value: '0.876' }
])

// 数据集性能对比
const datasetPerformance = ref([
  { dataset: '国家电网负荷数据 (2020-2022)', mse: '0.0234', mae: '0.0156', rmse: '0.1531', accuracy: 87.6 },
  { dataset: '南方电网用电量数据 (2019-2022)', mse: '0.0312', mae: '0.0189', rmse: '0.1766', accuracy: 85.2 },
  { dataset: '工业园区电力消耗数据 (2021-2023)', mse: '0.0278', mae: '0.0167', rmse: '0.1667', accuracy: 86.4 },
  { dataset: '北京市交通流量数据 (2020-2022)', mse: '0.0456', mae: '0.0234', rmse: '0.2135', accuracy: 79.8 }
])

// 获取模型列表
const fetchModels = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      per_page: pagination.pageSize,
      ...filterForm
    }
    
    const response = await modelAPI.getModels(params)
    if (response.success) {
      modelList.value = response.data.map(item => ({
        ...item,
        createdAt: formatDate(item.createdAt),
        updatedAt: formatDate(item.updatedAt)
      }))
      pagination.total = response.total
    } else {
      ElMessage.error(response.message || '获取模型列表失败')
    }
  } catch (error) {
    console.error('获取模型列表出错:', error)
    ElMessage.error('获取模型列表失败')
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

// 获取模型标签样式
const getModelTagType = (type) => {
  const types = {
    'CrossGNN': 'danger',
    'HDMixer': 'warning',
    'LeRet': 'success'
  }
  return types[type] || 'info'
}

// 处理筛选
const handleFilter = () => {
  pagination.currentPage = 1
  fetchModels()
}

// 重置筛选
const resetFilter = () => {
  filterForm.type = ''
  handleFilter()
}

// 处理分页大小变化
const handleSizeChange = (size) => {
  pagination.pageSize = size
  fetchModels()
}

// 处理页码变化
const handleCurrentChange = (page) => {
  pagination.currentPage = page
  fetchModels()
}

// 查看模型详情
const viewModelDetails = async (model) => {
  currentModel.value = { ...model }
  detailsDialogVisible.value = true
  detailsLoading.value = true
  
  try {
    const response = await modelAPI.getModelDetails(model.id)
    if (response.success) {
      currentModel.value = {
        ...currentModel.value,
        ...response.data,
        createdAt: formatDate(response.data.createdAt),
        updatedAt: formatDate(response.data.updatedAt)
      }
      
      // 处理超参数数据
      hyperParamsData.value = response.data.hyperParams || []
    } else {
      ElMessage.error(response.message || '获取模型详情失败')
    }
  } catch (error) {
    console.error('获取模型详情出错:', error)
    ElMessage.error('获取模型详情失败')
  } finally {
    detailsLoading.value = false
  }
}

// 配置模型
const configureModel = async (model) => {
  currentModel.value = { ...model }
  configDialogVisible.value = true
  
  try {
    const response = await modelAPI.getModelConfig(model.id)
    if (response.success) {
      configParams.value = response.data.params || []
      
      // 初始化配置表单
      const formData = {}
      configParams.value.forEach(param => {
        formData[param.key] = param.defaultValue
      })
      Object.assign(configForm, formData)
    } else {
      ElMessage.error(response.message || '获取模型配置失败')
    }
  } catch (error) {
    console.error('获取模型配置出错:', error)
    ElMessage.error('获取模型配置失败')
  }
}

// 保存模型配置
const saveModelConfig = async () => {
  try {
    const params = {
      modelId: currentModel.value.id,
      config: configForm
    }
    
    const response = await modelAPI.saveModelConfig(params)
    if (response.success) {
      ElMessage.success('模型配置保存成功')
      configDialogVisible.value = false
    } else {
      ElMessage.error(response.message || '保存模型配置失败')
    }
  } catch (error) {
    console.error('保存模型配置出错:', error)
    ElMessage.error('保存模型配置失败')
  }
}

// 查看模型性能
const viewModelPerformance = async (model) => {
  currentModel.value = { ...model }
  performanceDialogVisible.value = true
  performanceLoading.value = true
  
  try {
    const response = await modelAPI.getModelPerformance(model.id)
    if (response.success) {
      // 更新性能指标
      performanceMetrics.value = response.data.metrics || performanceMetrics.value
      
      // 更新数据集性能对比
      if (response.data.datasetPerformance) {
        datasetPerformance.value = response.data.datasetPerformance
      }
      
      // 渲染性能图表
      nextTick(() => {
        renderPerformanceChart(response.data.chartData || {})
      })
    } else {
      ElMessage.error(response.message || '获取模型性能数据失败')
    }
  } catch (error) {
    console.error('获取模型性能数据出错:', error)
    ElMessage.error('获取模型性能数据失败')
  } finally {
    performanceLoading.value = false
  }
}

// 渲染性能图表
const renderPerformanceChart = (chartData) => {
  if (performanceChart) {
    performanceChart.dispose()
  }
  
  performanceChart = echarts.init(performanceChartRef.value)
  
  const option = {
    title: {
      text: '模型性能趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['训练损失', '验证损失', '准确率'],
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: chartData.epochs || []
    },
    yAxis: [
      {
        type: 'value',
        name: '损失',
        position: 'left',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#5470C6'
          }
        },
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '准确率',
        position: 'right',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#91CC75'
          }
        },
        axisLabel: {
          formatter: '{value}%'
        }
      }
    ],
    series: [
      {
        name: '训练损失',
        type: 'line',
        data: chartData.trainLoss || [],
        smooth: true
      },
      {
        name: '验证损失',
        type: 'line',
        data: chartData.valLoss || [],
        smooth: true
      },
      {
        name: '准确率',
        type: 'line',
        yAxisIndex: 1,
        data: chartData.accuracy || [],
        smooth: true,
        lineStyle: {
          color: '#91CC75'
        },
        itemStyle: {
          color: '#91CC75'
        }
      }
    ]
  }
  
  performanceChart.setOption(option)
}

// 窗口大小变化时重新调整图表大小
const handleResize = () => {
  if (performanceChart) {
    performanceChart.resize()
  }
}

// 生命周期钩子
onMounted(() => {
  fetchModels()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (performanceChart) {
    performanceChart.dispose()
    performanceChart = null
  }
})
</script>

<style scoped>
.model-management-container {
  padding: 20px;
}

.model-card {
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

.model-details-container {
  padding: 10px;
}

.model-architecture {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
  margin: 10px 0;
  max-height: 300px;
  overflow-y: auto;
}

.model-architecture pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: 'Courier New', Courier, monospace;
  font-size: 14px;
  line-height: 1.5;
}

.performance-container {
  padding: 10px;
}

.performance-header {
  text-align: center;
  margin-bottom: 20px;
}

.metrics-cards {
  margin: 20px 0;
}

.metric-card {
  text-align: center;
  padding: 15px;
  transition: all 0.3s;
}

.metric-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 10px;
}

.metric-name {
  font-size: 16px;
  color: #606266;
}

.chart-container {
  height: 400px;
  width: 100%;
  margin: 20px 0;
}

.dataset-comparison {
  margin-top: 20px;
}

.dataset-comparison h4 {
  margin-bottom: 15px;
  font-weight: 600;
  color: #303133;
}
</style>