<template>
  <div class="not-found-container">
    <div class="not-found-card">
      <div class="not-found-header">
        <h2>时间序列预测可视化系统</h2>
        <p>404 - 页面未找到</p>
      </div>
      
      <div class="not-found-content">
        <el-icon class="not-found-icon"><WarningFilled /></el-icon>
        <p class="not-found-message">抱歉，您访问的页面不存在</p>
        <p class="not-found-desc">请检查您输入的网址是否正确，或返回首页继续浏览</p>
        
        <el-button type="primary" class="back-button" @click="goToDashboard">
          返回首页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { WarningFilled } from '@element-plus/icons-vue'

const router = useRouter()

const goToDashboard = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.not-found-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%);
}

.not-found-card {
  width: 500px;
  padding: 40px;
  border-radius: 8px;
  background-color: white;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.not-found-header {
  margin-bottom: 30px;
}

.not-found-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 10px;
}

.not-found-header p {
  font-size: 18px;
  font-weight: bold;
  color: #606266;
}

.not-found-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.not-found-icon {
  font-size: 80px;
  color: #e6a23c;
  margin-bottom: 20px;
}

.not-found-message {
  font-size: 20px;
  color: #303133;
  margin-bottom: 10px;
}

.not-found-desc {
  font-size: 14px;
  color: #909399;
  margin-bottom: 30px;
}

.back-button {
  width: 200px;
  padding: 12px 0;
  font-size: 16px;
}
</style>