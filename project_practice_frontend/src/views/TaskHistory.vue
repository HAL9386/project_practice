<template>
  <div class="task-history-container">
    <el-card class="task-card">
      <template #header>
        <div class="card-header">
          <span>预测任务历史</span>
        </div>
      </template>
      
      <!-- 任务筛选 -->
      <div class="filter-container">
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="任务状态">
            <el-select v-model="filterForm.status" placeholder="全部状态" clearable>
              <el-option label="运行中" value="running" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
            </el-select>
          </el-form-item>
          <el-form-item label="模型类型">
            <el-select v-model="filterForm.modelType" placeholder="全部模型" clearable>
              <el-option label="CrossGNN" value="CrossGNN" />
              <el-option label="HDMixer" value="HDMixer" />
              <el-option label="LeRet" value="LeRet" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="filterForm.timeRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleFilter">筛选</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 任务列表 -->
      <el-table
        v-loading="loading"
        :data="taskList"
        style="width: 100%"
        border
        :row-class-name="tableRowClassName"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="任务名称" min-width="180" />
        <el-table-column prop="modelType" label="模型类型" width="120">
          <template #default="scope">
            <el-tag :type="getModelTagType(scope.row.modelType)">
              {{ scope.row.modelType }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="datasetName" label="数据集" min-width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusTagType(scope.row.status)">
              {{ getStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="metrics.mse" label="MSE" width="100" />
        <el-table-column prop="metrics.mae" label="MAE" width="100" />
        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="scope">
            {{ scope.row.duration }}秒
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button type="text" size="small" @click="viewTaskDetails(scope.row)">详情</el-button>
            <el-button type="text" size="small" @click="viewTaskResult(scope.row)" :disabled="scope.row.status !== 'completed'">结果</el-button>
            <el-button type="text" size="small" @click="loadAsTemplate(scope.row)" :disabled="scope.row.status !== 'completed'">加载为模板</el-button>
            <el-button type="text" size="small" @click="rerunTask(scope.row)" :disabled="scope.row.status === 'running'">重新运行</el-button>
            <el-button 
              type="text" 
              size="small" 
              @click="deleteTask(scope.row)"
              :disabled="scope.row.status === 'running'"
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
    
    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="detailsDialogVisible"
      title="任务详情"
      width="60%"
    >
      <div v-loading="detailsLoading" class="task-details-container">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ currentTask.name }}</el-descriptions-item>
          <el-descriptions-item label="模型类型">{{ currentTask.modelType }}</el-descriptions-item>
          <el-descriptions-item label="数据集">{{ currentTask.datasetName }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ getStatusLabel(currentTask.status) }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentTask.createdAt }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ currentTask.completedAt || '-' }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ currentTask.duration }}秒</el-descriptions-item>
          <el-descriptions-item label="预测长度">{{ currentTask.hyperParams?.predictionLength || '-' }}</el-descriptions-item>
        </el-descriptions>
        
        <el-divider content-position="left">超参数配置</el-divider>
        
        <el-descriptions :column="3" border>
          <el-descriptions-item label="学习率">{{ currentTask.hyperParams?.learningRate || '-' }}</el-descriptions-item>
          <el-descriptions-item label="迭代次数">{{ currentTask.hyperParams?.epochs || '-' }}</el-descriptions-item>
          <el-descriptions-item label="批次大小">{{ currentTask.hyperParams?.batchSize || '-' }}</el-descriptions-item>
        </el-descriptions>
        
        <el-divider content-position="left">性能指标</el-divider>
        
        <el-descriptions :column="4" border>
          <el-descriptions-item label="MSE">{{ currentTask.metrics?.mse || '-' }}</el-descriptions-item>
          <el-descriptions-item label="MAE">{{ currentTask.metrics?.mae || '-' }}</el-descriptions-item>
          <el-descriptions-item label="RMSE">{{ currentTask.metrics?.rmse || '-' }}</el-descriptions-item>
          <el-descriptions-item label="可信度">{{ currentTask.metrics?.confidence || '-' }}</el-descriptions-item>
        </el-descriptions>
        
        <template v-if="currentTask.logs && currentTask.logs.length > 0">
          <el-divider content-position="left">任务日志</el-divider>
          
          <div class="task-logs">
            <el-timeline>
              <el-timeline-item
                v-for="(log, index) in currentTask.logs"
                :key="index"
                :timestamp="log.timestamp"
                :type="getLogTypeIcon(log.level)"
                :color="getLogTypeColor(log.level)"
              >
                {{ log.message }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </template>
      </div>
    </el-dialog>
    
    <!-- 任务结果对话框 -->
    <el-dialog
      v-model="resultDialogVisible"
      title="预测结果"
      width="80%"
    >
      <div v-loading="resultLoading" class="result-container">
        <div class="result-header">
          <h3>{{ currentTask.name }} 预测结果</h3>
        </div>
        
        <el-divider />
        
        <!-- 图表切换 -->
        <div class="chart-controls">
          <el-radio-group v-model="chartType" size="large">
            <el-radio-button label="line">折线图</el-radio-button>
            <el-radio-button label="error">误差图</el-radio-button>
            <el-radio-button label="comparison">对比图</el-radio-button>
          </el-radio-group>
          
          <el-button type="primary" size="small" @click="exportResult">导出结果</el-button>
        </div>
        
        <!-- 图表容器 -->
        <div class="chart-container" ref="resultChartRef"></div>
        
        <el-divider />
        
        <!-- 预测数据表格 -->
        <div class="result-table-container">
          <el-table
            :data="predictionData"
            style="width: 100%"
            border
            max-height="300px"
          >
            <el-table-column prop="timestamp" label="时间戳" width="180" />
            <el-table-column prop="actual" label="实际值" width="120" />
            <el-table-column prop="predicted" label="预测值" width="120" />
            <el-table-column prop="error" label="误差" width="120" />
            <el-table-column prop="errorPercent" label="误差百分比" width="120">
              <template #default="scope">
                {{ scope.row.errorPercent }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { predictionAPI } from '@/api'
import * as echarts from 'echarts'
import { useRouter } from 'vue-router'

// 获取路由实例
const router = useRouter()

// 状态变量
const loading = ref(false)
const detailsLoading = ref(false)
const resultLoading = ref(false)
const detailsDialogVisible = ref(false)
const resultDialogVisible = ref(false)
const taskList = ref([])
const resultChartRef = ref(null)
let resultChart = null
const chartType = ref('line')

// 当前选中的任务
const currentTask = ref({})

// 筛选表单
const filterForm = reactive({
  status: '',
  modelType: '',
  timeRange: []
})

// 分页信息
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 预测数据
const predictionData = ref([])

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      per_page: pagination.pageSize,
      status: filterForm.status || undefined,
      model_type: filterForm.modelType || undefined,
      start_date: filterForm.timeRange?.[0] || undefined,
      end_date: filterForm.timeRange?.[1] || undefined
    }
    
    const response = await predictionAPI.getTasks(params)
    if (response.success) {
      taskList.value = response.data.map(item => ({
        ...item,
        createdAt: formatDate(item.createdAt),
        completedAt: formatDate(item.completedAt)
      }))
      pagination.total = response.total
    } else {
      ElMessage.error(response.message || '获取任务列表失败')
    }
  } catch (error) {
    console.error('获取任务列表出错:', error)
    ElMessage.error('获取任务列表失败')
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

// 获取状态标签样式
const getStatusTagType = (status) => {
  const types = {
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return types[status] || 'info'
}

// 获取状态标签文本
const getStatusLabel = (status) => {
  const labels = {
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败'
  }
  return labels[status] || '未知状态'
}

// 获取日志类型图标
const getLogTypeIcon = (level) => {
  const icons = {
    'INFO': 'primary',
    'WARNING': 'warning',
    'ERROR': 'danger'
  }
  return icons[level] || 'info'
}

// 获取日志类型颜色
const getLogTypeColor = (level) => {
  const colors = {
    'INFO': '#409EFF',
    'WARNING': '#E6A23C',
    'ERROR': '#F56C6C'
  }
  return colors[level] || '#909399'
}

// 表格行样式
const tableRowClassName = ({ row }) => {
  if (row.status === 'failed') {
    return 'error-row'
  } else if (row.status === 'running') {
    return 'warning-row'
  }
  return ''
}

// 筛选处理
const handleFilter = () => {
  pagination.currentPage = 1
  fetchTasks()
}

// 重置筛选
const resetFilter = () => {
  filterForm.status = ''
  filterForm.modelType = ''
  filterForm.timeRange = []
  handleFilter()
}

// 分页大小变化
const handleSizeChange = (size) => {
  pagination.pageSize = size
  fetchTasks()
}

// 页码变化
const handleCurrentChange = (page) => {
  pagination.currentPage = page
  fetchTasks()
}

// 查看任务详情
const viewTaskDetails = async (task) => {
  currentTask.value = { ...task }
  detailsDialogVisible.value = true
  detailsLoading.value = true
  
  try {
    const response = await predictionAPI.getTask(task.id)
    if (response.success) {
      currentTask.value = {
        ...response.data,
        createdAt: formatDate(response.data.createdAt),
        completedAt: formatDate(response.data.completedAt)
      }
    } else {
      ElMessage.error(response.message || '获取任务详情失败')
    }
  } catch (error) {
    console.error('获取任务详情出错:', error)
    ElMessage.error('获取任务详情失败')
  } finally {
    detailsLoading.value = false
  }
}

// 查看任务结果
const viewTaskResult = async (task) => {
  if (task.status !== 'completed') {
    ElMessage.warning('只能查看已完成任务的结果')
    return
  }
  
  currentTask.value = { ...task }
  resultDialogVisible.value = true
  resultLoading.value = true
  
  try {
    // 使用getTask API获取任务详情，包括预测结果
    const response = await predictionAPI.getTask(task.id)
    if (response.success && response.data.predictions) {
      // 处理预测数据
      predictionData.value = response.data.predictions.map(item => ({
        timestamp: item.timestamp,
        actual: parseFloat(item.actual).toFixed(4),
        predicted: parseFloat(item.predicted).toFixed(4),
        error: parseFloat(Math.abs(item.actual - item.predicted)).toFixed(4),
        errorPercent: parseFloat(Math.abs(item.actual - item.predicted) / Math.abs(item.actual) * 100).toFixed(2)
      }))
      
      // 渲染图表
      setTimeout(() => {
        renderChart(response.data.predictions)
      }, 100)
    } else {
      ElMessage.error(response.message || '获取任务结果失败')
    }
  } catch (error) {
    console.error('获取任务结果出错:', error)
    ElMessage.error('获取任务结果失败')
  } finally {
    resultLoading.value = false
  }
}

// 渲染图表
const renderChart = (data) => {
  if (resultChart) {
    resultChart.dispose()
  }
  
  resultChart = echarts.init(resultChartRef.value)
  
  const timestamps = data.map(item => item.timestamp)
  const actualValues = data.map(item => parseFloat(item.actual))
  const predictedValues = data.map(item => parseFloat(item.predicted))
  const errorValues = data.map(item => Math.abs(parseFloat(item.actual) - parseFloat(item.predicted)))
  
  let option = {}
  
  if (chartType.value === 'line') {
    option = {
      title: {
        text: '预测结果折线图',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['实际值', '预测值'],
        bottom: 10
      },
      xAxis: {
        type: 'category',
        data: timestamps,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '值'
      },
      series: [
        {
          name: '实际值',
          type: 'line',
          data: actualValues,
          smooth: true,
          lineStyle: {
            width: 2
          }
        },
        {
          name: '预测值',
          type: 'line',
          data: predictedValues,
          smooth: true,
          lineStyle: {
            width: 2
          }
        }
      ]
    }
  } else if (chartType.value === 'error') {
    option = {
      title: {
        text: '预测误差图',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: timestamps,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '误差'
      },
      series: [
        {
          name: '误差',
          type: 'bar',
          data: errorValues,
          itemStyle: {
            color: '#F56C6C'
          }
        }
      ]
    }
  } else if (chartType.value === 'comparison') {
    option = {
      title: {
        text: '实际值与预测值对比',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'value',
        name: '实际值'
      },
      yAxis: {
        type: 'value',
        name: '预测值'
      },
      series: [
        {
          name: '对比',
          type: 'scatter',
          data: actualValues.map((actual, index) => [actual, predictedValues[index]]),
          itemStyle: {
            color: '#409EFF'
          }
        },
        {
          name: '理想线',
          type: 'line',
          data: (() => {
            const min = Math.min(...actualValues, ...predictedValues)
            const max = Math.max(...actualValues, ...predictedValues)
            return [[min, min], [max, max]]
          })(),
          lineStyle: {
            type: 'dashed'
          },
          showSymbol: false
        }
      ]
    }
  }
  
  resultChart.setOption(option)
}

// 监听图表类型变化
watch(chartType, () => {
  if (predictionData.value.length > 0 && resultChartRef.value) {
    const data = predictionData.value.map(item => ({
      timestamp: item.timestamp,
      actual: parseFloat(item.actual),
      predicted: parseFloat(item.predicted)
    }))
    renderChart(data)
  }
})

// 导出结果
const exportResult = () => {
  if (predictionData.value.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }
  
  // 创建CSV内容
  const headers = ['时间戳', '实际值', '预测值', '误差', '误差百分比(%)']
  const csvContent = [
    headers.join(','),
    ...predictionData.value.map(item => [
      item.timestamp,
      item.actual,
      item.predicted,
      item.error,
      item.errorPercent
    ].join(','))
  ].join('\n')
  
  // 创建下载链接
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `${currentTask.value.name}_预测结果.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success('导出成功')
}

// 重新运行任务
const rerunTask = async (task) => {
  if (task.status === 'running') {
    ElMessage.warning('任务正在运行中')
    return
  }
  
  try {
    const response = await predictionAPI.rerunTask(task.id)
    if (response.success) {
      ElMessage.success('任务已重新提交')
      fetchTasks()
    } else {
      ElMessage.error(response.message || '重新运行任务失败')
    }
  } catch (error) {
    console.error('重新运行任务出错:', error)
    ElMessage.error('重新运行任务失败')
  }
}

// 删除任务
const deleteTask = (task) => {
  if (task.status === 'running') {
    ElMessage.warning('无法删除运行中的任务')
    return
  }
  
  ElMessageBox.confirm(
    '确定要删除该任务吗？删除后无法恢复。',
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const response = await predictionAPI.deleteTask(task.id)
      if (response.success) {
        ElMessage.success('删除成功')
        fetchTasks()
      } else {
        ElMessage.error(response.message || '删除任务失败')
      }
    } catch (error) {
      console.error('删除任务出错:', error)
      ElMessage.error('删除任务失败')
    }
  }).catch(() => {
    // 取消删除
  })
}

// 窗口大小变化时重新渲染图表
const handleResize = () => {
  if (resultChart) {
    resultChart.resize()
  }
}

// 生命周期钩子
onMounted(() => {
  fetchTasks()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (resultChart) {
    resultChart.dispose()
    resultChart = null
  }
})
</script>

<style scoped>
.task-history-container {
  padding: 20px;
}

.task-card {
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

.task-details-container {
  padding: 10px;
}

.task-logs {
  margin-top: 20px;
  max-height: 300px;
  overflow-y: auto;
}

.result-container {
  padding: 10px;
}

.chart-container {
  height: 400px;
  margin: 20px 0;
}

.chart-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 10px 0;
}

.result-table-container {
  margin-top: 20px;
}

.delete-btn {
  color: #F56C6C;
}

/* 表格行样式 */
:deep(.error-row) {
  background-color: #fef0f0;
}

:deep(.warning-row) {
  background-color: #fdf6ec;
}
</style>

// 加载任务作为模板
const loadAsTemplate = (task) => {
  if (task.status !== 'completed') {
    ElMessage.warning('只能加载已完成的任务作为模板')
    return
  }
  
  // 使用路由导航到预测页面，并传递任务ID
  router.push({
    name: 'Prediction',
    query: { taskId: task.id }
  })
  
  ElMessage.success('正在加载任务配置...')
}