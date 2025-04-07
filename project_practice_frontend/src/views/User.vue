<template>
  <div class="user-container">
    <el-card class="user-card">
      <template #header>
        <div class="card-header">
          <span>用户中心</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <!-- 个人信息标签页 -->
        <el-tab-pane label="个人信息" name="profile">
          <el-form :model="profileForm" :rules="profileRules" ref="profileFormRef" label-width="100px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" />
            </el-form-item>
            <el-form-item label="真实姓名" prop="realName">
              <el-input v-model="profileForm.realName" />
            </el-form-item>
            <el-form-item label="所属机构" prop="organization">
              <el-input v-model="profileForm.organization" />
            </el-form-item>
            <el-form-item label="职位" prop="position">
              <el-input v-model="profileForm.position" />
            </el-form-item>
            <el-form-item label="个人简介" prop="bio">
              <el-input v-model="profileForm.bio" type="textarea" rows="4" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updateProfile" :loading="profileLoading">保存信息</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 修改密码标签页 -->
        <el-tab-pane label="修改密码" name="password">
          <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
            <el-form-item label="当前密码" prop="currentPassword">
              <el-input v-model="passwordForm.currentPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updatePassword" :loading="passwordLoading">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 系统设置标签页 -->
        <el-tab-pane label="系统设置" name="settings">
          <el-form :model="settingsForm" label-width="120px">
            <el-form-item label="界面主题">
              <el-radio-group v-model="settingsForm.theme">
                <el-radio label="light">浅色</el-radio>
                <el-radio label="dark">深色</el-radio>
                <el-radio label="system">跟随系统</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="默认数据集类型">
              <el-select v-model="settingsForm.defaultDatasetType" placeholder="请选择默认数据集类型">
                <el-option label="电力数据" value="power" />
                <el-option label="交通数据" value="traffic" />
                <el-option label="气候数据" value="climate" />
                <el-option label="自定义数据" value="custom" />
              </el-select>
            </el-form-item>
            <el-form-item label="默认预测模型">
              <el-select v-model="settingsForm.defaultModelType" placeholder="请选择默认预测模型">
                <el-option label="CrossGNN" value="CrossGNN" />
                <el-option label="HDMixer" value="HDMixer" />
                <el-option label="LeRet" value="LeRet" />
              </el-select>
            </el-form-item>
            <el-form-item label="图表显示设置">
              <el-checkbox v-model="settingsForm.showConfidenceInterval">显示置信区间</el-checkbox>
              <el-checkbox v-model="settingsForm.showDataPoints">显示数据点</el-checkbox>
              <el-checkbox v-model="settingsForm.smoothLine">平滑曲线</el-checkbox>
            </el-form-item>
            <el-form-item label="通知设置">
              <el-checkbox v-model="settingsForm.emailNotification">任务完成邮件通知</el-checkbox>
              <el-checkbox v-model="settingsForm.browserNotification">浏览器通知</el-checkbox>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSettings" :loading="settingsLoading">保存设置</el-button>
              <el-button @click="resetSettings">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 任务统计标签页 -->
        <el-tab-pane label="任务统计" name="statistics">
          <div class="statistics-container">
            <!-- 统计卡片 -->
            <el-row :gutter="20" class="stat-cards">
              <el-col :span="6" v-for="(stat, index) in userStats" :key="index">
                <el-card shadow="hover" class="stat-card">
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
            
            <!-- 任务统计图表 -->
            <div class="chart-container" ref="taskChartRef"></div>
            
            <!-- 模型使用统计 -->
            <el-divider content-position="left">模型使用统计</el-divider>
            <div class="model-usage-container" ref="modelUsageChartRef"></div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { authAPI, predictionAPI } from '@/api'
import * as echarts from 'echarts'

// 状态变量
const activeTab = ref('profile')
const profileLoading = ref(false)
const passwordLoading = ref(false)
const settingsLoading = ref(false)
const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const taskChartRef = ref(null)
const modelUsageChartRef = ref(null)
let taskChart = null
let modelUsageChart = null

// 个人信息表单
const profileForm = reactive({
  username: '',
  email: '',
  realName: '',
  organization: '',
  position: '',
  bio: ''
})

// 个人信息表单验证规则
const profileRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  realName: [
    { max: 50, message: '长度不能超过50个字符', trigger: 'blur' }
  ],
  organization: [
    { max: 100, message: '长度不能超过100个字符', trigger: 'blur' }
  ],
  position: [
    { max: 50, message: '长度不能超过50个字符', trigger: 'blur' }
  ],
  bio: [
    { max: 500, message: '长度不能超过500个字符', trigger: 'blur' }
  ]
}

// 修改密码表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 密码验证规则
const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能小于8个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 系统设置表单
const settingsForm = reactive({
  theme: 'light',
  defaultDatasetType: 'power',
  defaultModelType: 'CrossGNN',
  showConfidenceInterval: true,
  showDataPoints: false,
  smoothLine: true,
  emailNotification: true,
  browserNotification: false
})

// 用户统计数据
const userStats = reactive([
  { title: '总任务数', value: 24, icon: 'DataLine' },
  { title: '成功任务', value: 21, icon: 'Check' },
  { title: '失败任务', value: 3, icon: 'Close' },
  { title: '平均准确率', value: '87.5%', icon: 'Aim' }
])

// 获取用户信息
const fetchUserProfile = async () => {
  try {
    const response = await authAPI.getUserInfo()
    if (response.success) {
      const { username, email, profile } = response.data
      profileForm.username = username
      profileForm.email = email
      if (profile) {
        profileForm.realName = profile.realName || ''
        profileForm.organization = profile.organization || ''
        profileForm.position = profile.position || ''
        profileForm.bio = profile.bio || ''
      }
    } else {
      ElMessage.error(response.message || '获取用户信息失败')
    }
  } catch (error) {
    console.error('获取用户信息出错:', error)
    ElMessage.error('获取用户信息失败')
  }
}

// 获取用户设置
const fetchUserSettings = async () => {
  try {
    // 这里应该调用后端API获取用户设置
    // 模拟从本地存储获取设置
    const savedSettings = localStorage.getItem('userSettings')
    if (savedSettings) {
      const settings = JSON.parse(savedSettings)
      Object.assign(settingsForm, settings)
    }
  } catch (error) {
    console.error('获取用户设置出错:', error)
  }
}

// 获取用户统计数据
const fetchUserStatistics = async () => {
  try {
    const response = await predictionAPI.getTaskStatistics()
    if (response.success) {
      // 更新统计卡片数据
      userStats[0].value = response.data.totalTasks
      userStats[1].value = response.data.completedTasks
      userStats[2].value = response.data.failedTasks
      userStats[3].value = response.data.averageAccuracy + '%'
      
      // 初始化图表
      initTaskChart(response.data.tasksByDate)
      initModelUsageChart(response.data.modelUsage)
    }
  } catch (error) {
    console.error('获取用户统计数据出错:', error)
  }
}

// 更新个人信息
const updateProfile = () => {
  profileFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    profileLoading.value = true
    try {
      const response = await authAPI.updateProfile(profileForm)
      if (response.success) {
        ElMessage.success('个人信息更新成功')
      } else {
        ElMessage.error(response.message || '更新个人信息失败')
      }
    } catch (error) {
      console.error('更新个人信息出错:', error)
      ElMessage.error('更新个人信息失败')
    } finally {
      profileLoading.value = false
    }
  })
}

// 修改密码
const updatePassword = () => {
  passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    passwordLoading.value = true
    try {
      const response = await authAPI.changePassword({
        currentPassword: passwordForm.currentPassword,
        newPassword: passwordForm.newPassword
      })
      
      if (response.success) {
        ElMessage.success('密码修改成功')
        // 清空表单
        passwordForm.currentPassword = ''
        passwordForm.newPassword = ''
        passwordForm.confirmPassword = ''
        passwordFormRef.value.resetFields()
      } else {
        ElMessage.error(response.message || '密码修改失败')
      }
    } catch (error) {
      console.error('密码修改出错:', error)
      ElMessage.error('密码修改失败')
    } finally {
      passwordLoading.value = false
    }
  })
}

// 保存用户设置
const saveSettings = async () => {
  settingsLoading.value = true
  try {
    // 这里应该调用后端API保存用户设置
    // 模拟保存到本地存储
    localStorage.setItem('userSettings', JSON.stringify(settingsForm))
    ElMessage.success('设置保存成功')
  } catch (error) {
    console.error('保存设置出错:', error)
    ElMessage.error('保存设置失败')
  } finally {
    settingsLoading.value = false
  }
}

// 重置设置
const resetSettings = () => {
  // 重置为默认值
  Object.assign(settingsForm, {
    theme: 'light',
    defaultDatasetType: 'power',
    defaultModelType: 'CrossGNN',
    showConfidenceInterval: true,
    showDataPoints: false,
    smoothLine: true,
    emailNotification: true,
    browserNotification: false
  })
  ElMessage.info('已重置为默认设置')
}

// 初始化任务统计图表
const initTaskChart = (taskData) => {
  if (!taskChartRef.value) return
  
  // 销毁旧图表
  if (taskChart) {
    taskChart.dispose()
  }
  
  // 创建新图表
  taskChart = echarts.init(taskChartRef.value)
  
  // 处理数据
  const dates = taskData.map(item => item.date)
  const completedTasks = taskData.map(item => item.completed)
  const failedTasks = taskData.map(item => item.failed)
  
  // 配置图表选项
  const option = {
    title: {
      text: '近期任务统计',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['成功任务', '失败任务'],
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '成功任务',
        type: 'bar',
        stack: 'total',
        data: completedTasks,
        itemStyle: {
          color: '#67C23A'
        }
      },
      {
        name: '失败任务',
        type: 'bar',
        stack: 'total',
        data: failedTasks,
        itemStyle: {
          color: '#F56C6C'
        }
      }
    ]
  }
  
  // 设置图表选项并渲染
  taskChart.setOption(option)
  
  // 响应窗口大小变化
  window.addEventListener('resize', () => taskChart.resize())
}

// 初始化模型使用统计图表
const initModelUsageChart = (modelData) => {
  if (!modelUsageChartRef.value) return
  
  // 销毁旧图表
  if (modelUsageChart) {
    modelUsageChart.dispose()
  }
  
  // 创建新图表
  modelUsageChart = echarts.init(modelUsageChartRef.value)
  
  // 处理数据
  const models = modelData.map(item => item.name)
  const usageCounts = modelData.map(item => item.count)
  
  // 配置图表选项
  const option = {
    title: {
      text: '模型使用次数统计',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      data: models
    },
    series: [
      {
        name: '模型使用',
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
        data: models.map((name, index) => ({
          value: usageCounts[index],
          name: name
        }))
      }
    ]
  }
  
  // 设置图表选项并渲染
  modelUsageChart.setOption(option)
  
  // 响应窗口大小变化
  window.addEventListener('resize', () => modelUsageChart.resize())
}

// 生命周期钩子
onMounted(() => {
  // 获取用户信息
  fetchUserProfile()
  
  // 获取用户设置
  fetchUserSettings()
  
  // 获取用户统计数据
  fetchUserStatistics()
})

// 组件卸载时清理资源
onUnmounted(() => {
  // 销毁图表实例
  if (taskChart) {
    taskChart.dispose()
    taskChart = null
  }
  
  if (modelUsageChart) {
    modelUsageChart.dispose()
    modelUsageChart = null
  }
  
  // 移除事件监听器
  window.removeEventListener('resize', () => taskChart?.resize())
  window.removeEventListener('resize', () => modelUsageChart?.resize())
})

</script>

<style scoped>
.user-container {
  padding: 20px;
}

.user-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.register-form, .login-form {
  max-width: 500px;
  margin: 0 auto;
}

.register-button, .login-button {
  width: 100%;
  margin-top: 20px;
  margin-bottom: 15px;
}

.login-options {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
}

.statistics-container {
  margin-top: 20px;
}

.stat-cards {
  margin-bottom: 30px;
}

.stat-card {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 36px;
  margin-right: 15px;
  color: #409EFF;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-title {
  font-size: 14px;
  color: #909399;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-top: 5px;
}

.chart-container, .model-usage-container {
  height: 400px;
  margin: 20px 0;
}
</style>