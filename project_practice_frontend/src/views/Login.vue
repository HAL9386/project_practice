<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h2>时间序列预测可视化系统</h2>
        <p>登录您的账户</p>
      </div>
      
      <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" class="login-form">
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名" 
            prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="密码" 
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <div class="login-options">
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
          <el-button type="text" @click="forgotPassword">忘记密码?</el-button>
        </div>
        
        <el-button type="primary" class="login-button" :loading="loading" @click="handleLogin">
          登录
        </el-button>
        
        <div class="register-link">
          还没有账户? <el-button type="text" @click="goToRegister">立即注册</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/api'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应为6-20个字符', trigger: 'blur' }
  ]
}

const handleLogin = () => {
  loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    
    try {
      // 调用后端API进行登录验证
      const response = await authAPI.login({
        username: loginForm.username,
        password: loginForm.password
      })
      
      if (response.success) {
        // 存储登录信息
        localStorage.setItem('token', response.token)
        localStorage.setItem('userInfo', JSON.stringify(response.user))
        
        ElMessage.success('登录成功')
        router.push('/')
      } else {
        ElMessage.error(response.message || '登录失败')
      }
    } catch (error) {
      ElMessage.error('登录失败: ' + (error.response?.data?.message || error.message || '未知错误'))
    } finally {
      loading.value = false
    }
  })
}

const goToRegister = () => {
  router.push('/register')
}

const forgotPassword = () => {
  ElMessage.info('密码重置功能开发中')
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  border-radius: 8px;
  background-color: white;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 10px;
}

.login-header p {
  font-size: 14px;
  color: #909399;
}

.login-form {
  margin-top: 20px;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.login-button {
  width: 100%;
  padding: 12px 0;
  font-size: 16px;
  margin-bottom: 20px;
}

.register-link {
  text-align: center;
  font-size: 14px;
  color: #606266;
}
</style>