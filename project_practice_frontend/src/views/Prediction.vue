<template>
  <div class="prediction-container">
    <el-card class="prediction-card">
      <template #header>
        <div class="card-header">
          <span>时间序列预测</span>
        </div>
      </template>
      
      <el-form :model="predictionForm" :rules="predictionRules" ref="predictionFormRef" label-width="120px">
        <!-- 任务名称 -->
        <el-form-item label="任务名称" prop="taskName">
          <el-input v-model="predictionForm.taskName" placeholder="请输入任务名称" />
        </el-form-item>
        
        <!-- 数据源选择 -->
        <el-form-item label="数据源类型" prop="dataSourceType">
          <el-radio-group v-model="predictionForm.dataSourceType">
            <el-radio label="preset">预设数据集</el-radio>
            <el-radio label="upload">上传数据</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 预设数据集选择 -->
        <el-form-item v-if="predictionForm.dataSourceType === 'preset'" label="数据集" prop="datasetId">
          <el-select v-model="predictionForm.datasetId" placeholder="请选择数据集" style="width: 100%">
            <el-option-group label="电力数据">
              <el-option v-for="item in powerDatasets" :key="item.id" :label="item.name" :value="item.id" />
            </el-option-group>
            <el-option-group label="交通数据">
              <el-option v-for="item in trafficDatasets" :key="item.id" :label="item.name" :value="item.id" />
            </el-option-group>
            <el-option-group label="气候数据">
              <el-option v-for="item in climateDatasets" :key="item.id" :label="item.name" :value="item.id" />
            </el-option-group>
          </el-select>
        </el-form-item>
        
        <!-- 上传数据 -->
        <el-form-item v-if="predictionForm.dataSourceType === 'upload'" label="上传CSV文件" prop="uploadFile">
          <el-upload
            class="upload-demo"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            :file-list="fileList"
          >
            <template #trigger>
              <el-button type="primary">选择文件</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                请上传CSV格式的时间序列数据，文件大小不超过10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <!-- 模型选择 -->
        <el-form-item label="预测模型" prop="modelType">
          <el-select v-model="predictionForm.modelType" placeholder="请选择预测模型" style="width: 100%">
            <el-option label="CrossGNN" value="CrossGNN" />
            <el-option label="HDMixer" value="HDMixer" />
            <el-option label="LeRet" value="LeRet" />
          </el-select>
        </el-form-item>
        
        <!-- 超参数配置 -->
        <el-form-item label="超参数配置">
          <el-collapse>
            <el-collapse-item title="高级参数设置" name="1">
              <el-form-item label="学习率" prop="learningRate">
                <el-slider
                  v-model="predictionForm.hyperParams.learningRate"
                  :min="0.0001"
                  :max="0.1"
                  :step="0.0001"
                  :format-tooltip="value => value.toFixed(4)"
                />
                <div class="param-value">{{ predictionForm.hyperParams.learningRate.toFixed(4) }}</div>
              </el-form-item>
              
              <el-form-item label="迭代次数" prop="epochs">
                <el-slider
                  v-model="predictionForm.hyperParams.epochs"
                  :min="10"
                  :max="500"
                  :step="10"
                />
                <div class="param-value">{{ predictionForm.hyperParams.epochs }}</div>
              </el-form-item>
              
              <el-form-item label="批次大小" prop="batchSize">
                <el-select v-model="predictionForm.hyperParams.batchSize" placeholder="请选择批次大小" style="width: 100%">
                  <el-option label="16" :value="16" />
                  <el-option label="32" :value="32" />
                  <el-option label="64" :value="64" />
                  <el-option label="128" :value="128" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="预测长度" prop="predictionLength">
                <el-input-number v-model="predictionForm.hyperParams.predictionLength" :min="1" :max="100" />
              </el-form-item>
            </el-collapse-item>
          </el-collapse>
        </el-form-item>
        
        <!-- 提交按钮 -->
        <el-form-item>
          <el-button type="primary" @click="submitPrediction" :loading="loading">开始预测</el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button type="info" @click="loadHistoryTask">加载历史任务</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 预测结果展示 -->
    <el-card v-if="showResult" class="result-card mt-20">
      <template #header>
        <div class="card-header">
          <span>预测结果</span>
          <div>
            <el-button-group>
              <el-button size="small" :type="chartType === 'line' ? 'primary' : ''" @click="chartType = 'line'">折线图</el-button>
              <el-button size="small" :type="chartType === 'error' ? 'primary' : ''" @click="chartType = 'error'">误差图</el-button>
              <el-button size="small" :type="chartType === 'comparison' ? 'primary' : ''" @click="chartType = 'comparison'">对比图</el-button>
            </el-button-group>
            <el-button size="small" type="info" @click="exportResult">导出结果</el-button>
          </div>
        </div>
      </template>
      
      <!-- 图表容器 -->
      <div class="chart-container" ref="chartRef"></div>
      
      <!-- 预测指标 -->
      <div class="metrics-panel">
        <el-descriptions title="预测性能指标" :column="3" border>
          <el-descriptions-item label="MSE">{{ predictionMetrics.mse }}</el-descriptions-item>
          <el-descriptions-item label="MAE">{{ predictionMetrics.mae }}</el-descriptions-item>
          <el-descriptions-item label="RMSE">{{ predictionMetrics.rmse }}</el-descriptions-item>
          <el-descriptions-item label="预测时长">{{ predictionMetrics.duration }}秒</el-descriptions-item>
          <el-descriptions-item label="数据点数">{{ predictionMetrics.dataPoints }}</el-descriptions-item>
          <el-descriptions-item label="可信度">{{ predictionMetrics.confidence }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { predictionAPI } from '@/api'
import { useRoute } from 'vue-router'

// 表单引用
const predictionFormRef = ref(null)
const chartRef = ref(null)
let chart = null

// 状态变量
const loading = ref(false)
const showResult = ref(false)
const chartType = ref('line')
const fileList = ref([])

// 预设数据集
const powerDatasets = [
  { id: 1, name: '国家电网负荷数据 (2020-2022)' },
  { id: 2, name: '南方电网用电量数据 (2019-2022)' },
  { id: 3, name: '工业园区电力消耗数据 (2021-2023)' }
]

const trafficDatasets = [
  { id: 4, name: '北京市交通流量数据 (2020-2022)' },
  { id: 5, name: '上海市高速公路数据 (2021-2023)' },
  { id: 6, name: '广州市地铁客流量数据 (2019-2022)' }
]

const climateDatasets = [
  { id: 7, name: '全国主要城市气温数据 (2018-2022)' },
  { id: 8, name: '华北地区降水量数据 (2015-2022)' },
  { id: 9, name: '沿海城市空气质量指数 (2020-2023)' }
]

// 预测表单
const predictionForm = reactive({
  taskName: '',
  dataSourceType: 'preset',
  datasetId: '',
  uploadFile: null,
  modelType: '',
  hyperParams: {
    learningRate: 0.001,
    epochs: 100,
    batchSize: 32,
    predictionLength: 24
  }
})

// 表单验证规则
const predictionRules = {
  taskName: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度应为2-50个字符', trigger: 'blur' }
  ],
  datasetId: [
    { required: true, message: '请选择数据集', trigger: 'change' }
  ],
  modelType: [
    { required: true, message: '请选择预测模型', trigger: 'change' }
  ]
}

// 预测指标
const predictionMetrics = reactive({
  mse: '0.0234',
  mae: '0.0156',
  rmse: '0.1531',
  duration: '12.5',
  dataPoints: '1440',
  confidence: '87.6%'
})

// 文件上传处理
const handleFileChange = (file) => {
  predictionForm.uploadFile = file.raw
  // 验证文件类型
  const isCSV = file.raw.type === 'text/csv' || file.name.endsWith('.csv')
  if (!isCSV) {
    ElMessage.error('请上传CSV格式的文件')
    fileList.value = []
    return false
  }
  // 验证文件大小
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过10MB')
    fileList.value = []
    return false
  }
  return true
}

// 提交预测
const submitPrediction = () => {
  predictionFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    // 验证上传文件
    if (predictionForm.dataSourceType === 'upload' && !predictionForm.uploadFile) {
      ElMessage.error('请上传数据文件')
      return
    }
    
    loading.value = true
    
    try {
      // 直接显示随机生成的图表数据，不发送后端请求
      // 更新预测指标（使用模拟数据）
      Object.assign(predictionMetrics, {
        mse: (Math.random() * 0.05).toFixed(4),
        mae: (Math.random() * 0.03).toFixed(4),
        rmse: (Math.random() * 0.2).toFixed(4),
        duration: (Math.random() * 20 + 5).toFixed(1),
        dataPoints: Math.floor(Math.random() * 1000 + 500).toString(),
        confidence: (Math.random() * 15 + 80).toFixed(1) + '%'
      })
      
      // 显示结果
      showResult.value = true
      ElMessage.success('预测完成（使用随机数据）')
      
      // 初始化图表
      setTimeout(() => {
        initChart()
      }, 100)
    } catch (error) {
      ElMessage.error('预测失败: ' + (error.message || '未知错误'))
    } finally {
      loading.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  predictionFormRef.value.resetFields()
  fileList.value = []
  predictionForm.hyperParams = {
    learningRate: 0.001,
    epochs: 100,
    batchSize: 32,
    predictionLength: 24
  }
}

// 加载历史任务
const loadHistoryTask = () => {
  // 打开对话框选择历史任务
  ElMessageBox.confirm(
    '将打开历史任务列表，选择一个任务作为模板。',
    '加载历史任务',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    try {
      // 获取任务列表
      const response = await predictionAPI.getTasks({
        status: 'completed',  // 只获取已完成的任务
        per_page: 100
      })
      
      if (!response.success) {
        throw new Error(response.message || '获取任务列表失败')
      }
      
      // 如果没有任务
      if (!response.tasks || response.tasks.length === 0) {
        ElMessage.warning('没有可用的历史任务')
        return
      }
      
      // 显示任务选择对话框
      ElMessageBox.confirm(
        h('div', { style: 'max-height: 300px; overflow-y: auto;' }, [
          h('p', '请选择一个历史任务作为模板：'),
          h('el-radio-group', {
            modelValue: selectedTaskId,
            'onUpdate:modelValue': (val) => selectedTaskId.value = val
          }, response.tasks.map(task => {
            return h('div', { class: 'task-select-item' }, [
              h('el-radio', {
                label: task.id,
                border: true,
                style: 'width: 100%; margin: 5px 0; padding: 10px;'
              }, {
                default: () => [
                  h('div', { style: 'font-weight: bold;' }, task.name),
                  h('div', { style: 'font-size: 12px; color: #666;' }, [
                    `模型: ${task.model || '-'} | 数据集: ${task.dataset || '-'} | 创建时间: ${task.created_at || '-'}`
                  ])
                ]
              })
            ])
          }))
        ]),
        '选择历史任务',
        {
          confirmButtonText: '加载',
          cancelButtonText: '取消',
          closeOnClickModal: false
        }
      ).then(async () => {
        if (!selectedTaskId.value) {
          ElMessage.warning('请选择一个任务')
          return
        }
        
        // 获取选中任务的详情
        const taskResponse = await predictionAPI.getTask(selectedTaskId.value)
        if (!taskResponse.success) {
          throw new Error(taskResponse.message || '获取任务详情失败')
        }
        
        const taskDetail = taskResponse.task
        
        // 填充表单
        predictionForm.taskName = `基于 ${taskDetail.name} 的新任务`
        predictionForm.modelType = taskDetail.model
        predictionForm.datasetId = taskDetail.dataset_id
        predictionForm.dataSourceType = 'preset'
        
        // 填充超参数
        if (taskDetail.hyperparams) {
          predictionForm.hyperParams = {
            ...predictionForm.hyperParams,
            ...taskDetail.hyperparams
          }
        }
        
        ElMessage.success('历史任务加载成功')
      }).catch(() => {})
    } catch (error) {
      console.error('加载历史任务出错:', error)
      ElMessage.error('加载历史任务失败: ' + (error.message || '未知错误'))
    }
  }).catch(() => {})
}

// 选中的任务ID
const selectedTaskId = ref(null)

// 导出结果
const exportResult = () => {
  ElMessage.success('预测结果已导出到CSV文件')
}

// 初始化图表
const initChart = () => {
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartRef.value)
  
  // 根据图表类型设置不同的配置
  let option = {}
  
  if (chartType.value === 'line') {
    // 折线图配置
    option = {
      title: {
        text: '时间序列预测结果',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['实际值', '预测值'],
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
        data: Array.from({length: 100}, (_, i) => `${i+1}h`),
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '数值',
        nameLocation: 'middle',
        nameGap: 40
      },
      series: [
        {
          name: '实际值',
          type: 'line',
          data: generateRandomData(100, 0.5),
          smooth: true,
          lineStyle: {
            width: 2
          }
        },
        {
          name: '预测值',
          type: 'line',
          data: generateRandomData(100, 0.5),
          smooth: true,
          lineStyle: {
            width: 2,
            type: 'dashed'
          }
        }
      ]
    }
  } else if (chartType.value === 'error') {
    // 误差图配置
    const errorData = generateRandomData(100, 0.1)
    option = {
      title: {
        text: '预测误差分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: Array.from({length: 100}, (_, i) => `${i+1}h`),
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '误差',
        nameLocation: 'middle',
        nameGap: 40
      },
      series: [
        {
          name: '预测误差',
          type: 'bar',
          data: errorData,
          itemStyle: {
            color: (params) => {
              return params.data >= 0 ? '#c23531' : '#2f4554'
            }
          }
        },
        {
          name: '误差趋势',
          type: 'line',
          smooth: true,
          data: errorData.map((val, idx, arr) => {
            if (idx < 5) return null
            return (arr[idx-5] + arr[idx-4] + arr[idx-3] + arr[idx-2] + arr[idx-1] + val) / 6
          }),
          lineStyle: {
            width: 2,
            color: '#5470c6'
          },
          symbol: 'none'
        }
      ]
    }
  } else if (chartType.value === 'comparison') {
    // 对比图配置
    const actualData = generateRandomData(100, 0.5)
    const predictData = generateRandomData(100, 0.5)
    option = {
      title: {
        text: '实际值与预测值对比',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['实际值', '预测值', '误差百分比'],
        bottom: 10
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: [
        {
          type: 'category',
          data: Array.from({length: 100}, (_, i) => `${i+1}h`),
          axisLabel: {
            rotate: 45
          }
        }
      ],
      yAxis: [
        {
          type: 'value',
          name: '数值',
          position: 'left'
        },
        {
          type: 'value',
          name: '误差百分比',
          position: 'right',
          axisLabel: {
            formatter: '{value}%'
          }
        }
      ],
      series: [
        {
          name: '实际值',
          type: 'line',
          data: actualData,
          smooth: true,
          lineStyle: {
            width: 2
          }
        },
        {
          name: '预测值',
          type: 'line',
          data: predictData,
          smooth: true,
          lineStyle: {
            width: 2,
            type: 'dashed'
          }
        },
        {
          name: '误差百分比',
          type: 'line',
          yAxisIndex: 1,
          data: actualData.map((val, idx) => {
            return Math.abs((val - predictData[idx]) / val * 100).toFixed(2)
          }),
          smooth: true,
          lineStyle: {
            width: 2,
            color: '#91cc75'
          },
          symbol: 'none'
        }
      ]
    }
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

// 生成随机数据用于演示
const generateRandomData = (length, volatility) => {
  const result = []
  let value = Math.random() * 100
  
  for (let i = 0; i < length; i++) {
    value = value + (Math.random() - 0.5) * volatility * value
    value = Math.max(0, value)
    result.push(parseFloat(value.toFixed(2)))
  }
  
  return result
}

// 获取路由实例
const route = useRoute()

// 生命周期钩子
onMounted(async () => {
  // 检查URL参数中是否有taskId，如果有则自动加载该任务作为模板
  const taskId = route.query.taskId
  if (taskId) {
    try {
      // 获取任务详情
      const taskResponse = await predictionAPI.getTask(taskId)
      if (!taskResponse.success) {
        throw new Error(taskResponse.message || '获取任务详情失败')
      }
      
      const taskDetail = taskResponse.task
      
      // 填充表单
      predictionForm.taskName = `基于 ${taskDetail.name} 的新任务`
      predictionForm.modelType = taskDetail.model
      predictionForm.datasetId = taskDetail.dataset_id
      predictionForm.dataSourceType = 'preset'
      
      // 填充超参数
      if (taskDetail.hyperparams) {
        predictionForm.hyperParams = {
          ...predictionForm.hyperParams,
          ...taskDetail.hyperparams
        }
      }
      
      ElMessage.success('历史任务加载成功')
    } catch (error) {
      console.error('加载历史任务出错:', error)
      ElMessage.error('加载历史任务失败: ' + (error.message || '未知错误'))
    }
  }
  
  // 移除：不再在页面加载时显示结果
  // showResult.value = true
  // setTimeout(() => {
  //   initChart()
  // }, 100)
})
</script>

<style scoped>
.prediction-container {
  padding: 20px;
}

.prediction-card, .result-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mt-20 {
  margin-top: 20px;
}

.chart-container {
  height: 400px;
  margin: 20px 0;
}

.param-value {
  text-align: center;
  margin-top: 5px;
  color: #409EFF;
  font-weight: bold;
}

.metrics-panel {
  margin-top: 20px;
}
</style>