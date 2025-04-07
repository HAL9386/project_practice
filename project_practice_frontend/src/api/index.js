import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 从localStorage获取token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('响应错误:', error)
    if (error.response && error.response.status === 401) {
      // 未授权，清除token并跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 用户认证相关API
export const authAPI = {
  // 用户登录
  login(data) {
    return api.post('/auth/login', data)
  },
  
  // 用户注册
  register(data) {
    return api.post('/auth/register', data)
  },
  
  // 获取用户信息
  getUserInfo() {
    return api.get('/auth/profile')
  },
  
  // 修改密码
  changePassword(data) {
    return api.post('/auth/change-password', data)
  }
}

// 数据集相关API
export const datasetAPI = {
  // 获取数据集列表
  getDatasets(params) {
    return api.get('/dataset', { params })
  },
  
  // 获取单个数据集详情
  getDataset(id) {
    return api.get(`/dataset/${id}`)
  },
  
  // 上传数据集
  uploadDataset(formData) {
    return api.post('/dataset', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 删除数据集
  deleteDataset(id) {
    return api.delete(`/dataset/${id}`)
  }
}

// 预测模型相关API
export const modelAPI = {
  // 获取模型列表
  getModels(params) {
    return api.get('/model', { params })
  },
  
  // 获取单个模型详情
  getModel(id) {
    return api.get(`/model/${id}`)
  },
  
  // 获取模型类型
  getModelTypes() {
    return api.get('/model/types')
  }
}

// 预测任务相关API
export const predictionAPI = {
  // 执行预测
  predict(data) {
    return api.post('/prediction/predict', data)
  },
  
  // 获取任务列表
  getTasks(params) {
    return api.get('/task', { params })
  },
  
  // 获取单个任务详情
  getTask(id) {
    return api.get(`/task/${id}`)
  },
  
  // 删除任务
  deleteTask(id) {
    return api.delete(`/task/${id}`)
  },
  
  // 重新运行任务
  rerunTask(id) {
    return api.post(`/task/${id}/rerun`)
  },
  
  // 获取任务统计信息
  getTaskStatistics() {
    return api.get('/task/statistics')
  },
  
  // 上传数据集
  uploadDataset(formData) {
    return api.post('/dataset', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }

}

// 导出所有API
export default {
  auth: authAPI,
  dataset: datasetAPI,
  model: modelAPI,
  prediction: predictionAPI
}