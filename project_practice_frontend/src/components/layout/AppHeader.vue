<template>
  <div class="header-container">
    <div class="logo-container">
      <img src="@/assets/logo.png" alt="Logo" class="logo" v-if="false" />
      <h1 class="title">时间序列预测可视化系统</h1>
    </div>
    <div class="header-right">
      <el-dropdown trigger="click" @command="handleCommand">
        <span class="user-info">
          <el-avatar :size="32" icon="UserFilled" />
          <span class="username">{{ username }}</span>
          <el-icon><CaretBottom /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>个人中心
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>系统设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('管理员')

onMounted(() => {
  // 从本地存储或API获取用户信息
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    try {
      const parsedInfo = JSON.parse(userInfo)
      username.value = parsedInfo.username || '用户'
    } catch (e) {
      console.error('解析用户信息失败', e)
    }
  }
})

const handleCommand = (command) => {
  if (command === 'logout') {
    // 清除登录信息
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    // 跳转到登录页
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/user')
  } else if (command === 'settings') {
    // 打开设置对话框或页面
    ElMessage.info('系统设置功能开发中')
  }
}
</script>

<style scoped>
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.logo-container {
  display: flex;
  align-items: center;
}

.logo {
  height: 40px;
  margin-right: 10px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: white;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: white;
}

.username {
  margin: 0 8px;
  font-size: 14px;
}
</style>