<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h2>时间序列预测可视化系统</h2>
        <p>创建新账户</p>
      </div>
      
      <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" class="register-form">
        <el-form-item prop="username">
          <el-input 
            v-model="registerForm.username" 
            placeholder="用户名" 
            prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="email">
          <el-input 
            v-model="registerForm.email" 
            placeholder="邮箱" 
            prefix-icon="Message"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="registerForm.password" 
            type="password" 
            placeholder="密码" 
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item prop="confirmPassword">
          <el-input 
            v-model="registerForm.confirmPassword" 
            type="password" 
            placeholder="确认密码" 
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-button type="primary" class="register-button" :loading="loading" @click="handleRegister">
          注册
        </el-button>
        
        <div class="login-link">
          已有账户? <el-button type="text" @click="goToLogin">立即登录</el-button>
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
const registerFormRef = ref(null)
const loading = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 自定义校验规则：确认密码
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应为6-20个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = () => {
  registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    
    try {
      // 调用后端API进行注册
      const response = await authAPI.register({
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password
      })
      
      if (response.success) {
        ElMessage.success('注册成功，请登录')
        router.push('/login')
      } else {
        ElMessage.error(response.message || '注册失败')
      }
    } catch (error) {
      ElMessage.error('注册失败: ' + (error.response?.data?.message || error.message || '未知错误'))
    } finally {
      loading.value = false
    }
  })
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%);
}

.register-card {
  width: 400px;
  padding: 40px;
  border-radius: 8px;
  background-color: white;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 10px;
}

.register-header p {
  font-size: 14px;
  color: #909399;
}

.register-form {
  margin-top: 20px;
}

.register-button {
  width: 100%;
  padding: 12px 0;
  font-size: 16px;
  margin-bottom: 20px;
}

.login-link {
  text-align: center;
  font-size: 14px;
  color: #606266;
}
</style>