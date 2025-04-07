<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :xs="24" :sm="12" :md="6" v-for="(stat, index) in statistics" :key="index">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon">
            <el-icon><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-title">{{ stat.title }}</div>
            <div class="stat-value">{{ stat.value }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <!-- 最近预测任务 -->
      <el-col :xs="24" :lg="16">
        <el-card shadow="hover" class="full-height-card">
          <template #header>
            <div class="card-header">
              <span>最近预测任务</span>
              <el-button type="primary" size="small" @click="goToNewPrediction">新建预测</el-button>
            </div>
          </template>
          <el-table :data="recentTasks" style="width: 100%" :row-class-name="tableRowClassName">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="任务名称" />
            <el-table-column prop="model" label="预测模型" />
            <el-table-column prop="dataset" label="数据集" />
            <el-table-column prop="createTime" label="创建时间" />
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button type="text" size="small" @click="viewTask(scope.row)">查看</el-button>
                <el-button type="text" size="small" @click="rerunTask(scope.row)">重新运行</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 性能指标 -->
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover" class="full-height-card">
          <template #header>
            <div class="card-header">
              <span>模型性能指标</span>
              <el-button type="text" @click="refreshMetrics">刷新</el-button>
            </div>
          </template>
          <div class="metrics-container" ref="metricsChart"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <!-- 系统日志 -->
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>系统日志</span>
              <el-button type="text" @click="clearLogs">清空</el-button>
            </div>
          </template>
          <el-table :data="systemLogs" style="width: 100%" height="250">
            <el-table-column prop="time" label="时间" width="180" />
            <el-table-column prop="level" label="级别" width="100">
              <template #default="scope">
                <el-tag :type="getLogLevelType(scope.row.level)" size="small">{{ scope.row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="module" label="模块" width="150" />
            <el-table-column prop="message" label="消息" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const metricsChart = ref(null)
let chart = null

// 统计数据
const statistics = reactive([
  { title: '预测任务总数', value: '128', icon: 'DataLine' },
  { title: '数据集数量', value: '36', icon: 'Files' },
  { title: '模型数量', value: '8', icon: 'SetUp' },
  { title: '活跃用户', value: '24', icon: 'User' }
])

// 最近任务数据
const recentTasks = ref([
  { id: 1, name: '北京空气质量预测', model: 'CrossGNN', dataset: '空气质量数据集', createTime: '2023-08-15 14:30', status: '完成' },
  { id: 2, name: '上海交通流量预测', model: 'HDMixer', dataset: '交通流量数据集', createTime: '2023-08-14 09:15', status: '完成' },
  { id: 3, name: '广州电力负荷预测', model: 'LeRet', dataset: '电力负荷数据集', createTime: '2023-08-13 16:45', status: '失败' },
  { id: 4, name: '深圳气温变化预测', model: 'CrossGNN', dataset: '气象数据集', createTime: '2023-08-12 11:20', status: '进行中' },
  { id: 5, name: '成都降雨量预测', model: 'HDMixer', dataset: '降雨量数据集', createTime: '2023-08-11 13:50', status: '完成' }
])

// 系统日志
const systemLogs = ref([
  { time: '2023-08-15 15:42:30', level: 'INFO', module: '系统', message: '用户admin登录系统' },
  { time: '2023-08-15 15:30:12', level: 'INFO', module: '预测任务', message: '任务ID:1 预测完成，MSE: 0.0234' },
  { time: '2023-08-15 15:28:45', level: 'INFO', module: '预测任务', message: '任务ID:1 开始执行预测' },
  { time: '2023-08-15 15:28:30', level: 'INFO', module: '数据管理', message: '加载数据集: 空气质量数据集' },
  { time: '2023-08-15 14:56:22', level: 'ERROR', module: '预测任务', message: '任务ID:3 执行失败: 内存不足' },
  { time: '2023-08-15 14:45:10', level: 'WARNING', module: '系统', message: '系统负载较高，建议优化任务调度' },
  { time: '2023-08-15 14:30:05', level: 'INFO', module: '用户管理', message: '新用户zhang_san注册成功' }
])

// 表格行样式
const tableRowClassName = ({ row }) => {
  if (row.status === '失败') {
    return 'error-row'
  }
  return ''
}

// 获取状态标签类型
const getStatusType = (status) => {
  switch (status) {
    case '完成': return 'success'
    case '进行中': return 'primary'
    case '失败': return 'danger'
    default: return 'info'
  }
}

// 获取日志级别标签类型
const getLogLevelType = (level) => {
  switch (level) {
    case 'INFO': return 'info'
    case 'WARNING': return 'warning'
    case 'ERROR': return 'danger'
    default: return 'info'
  }
}

// 初始化图表
const initChart = () => {
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(metricsChart.value)
  
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '模型性能',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { value: 0.023, name: 'CrossGNN (MSE)' },
          { value: 0.031, name: 'HDMixer (MSE)' },
          { value: 0.028, name: 'LeRet (MSE)' }
        ]
      }
    ]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

// 刷新性能指标
const refreshMetrics = () => {
  ElMessage.success('性能指标已更新')
  initChart()
}

// 清空日志
const clearLogs = () => {
  ElMessageBox.confirm('确定要清空所有日志记录吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    systemLogs.value = []
    ElMessage.success('日志已清空')
  }).catch(() => {})
}

// 查看任务详情
const viewTask = (task) => {
  router.push({
    path: '/task-history',
    query: { id: task.id }
  })
}

// 重新运行任务
const rerunTask = (task) => {
  ElMessage.success(`任务 "${task.name}" 已重新提交`)
}

// 跳转到新建预测页面
const goToNewPrediction = () => {
  router.push('/prediction')
}

onMounted(() => {
  // 初始化图表
  initChart()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.stat-card {
  display: flex;
  height: 100px;
  margin-bottom: 20px;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 60px;
  font-size: 24px;
  color: var(--primary-color);
}

.stat-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.full-height-card {
  height: 400px;
}

.metrics-container {
  height: 340px;
}

.error-row {
  --el-table-tr-bg-color: var(--el-color-danger-light-9);
}
</style>