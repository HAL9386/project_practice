<template>
  <div class="sidebar-container">
    <el-menu
      :default-active="activeMenu"
      class="el-menu-vertical"
      :collapse="isCollapse"
      :collapse-transition="false"
      router
      background-color="#ffffff"
      text-color="#303133"
      active-text-color="#409EFF"
    >
      <div class="menu-header">
        <el-button 
          type="text" 
          :icon="isCollapse ? 'Expand' : 'Fold'" 
          @click="toggleCollapse"
          class="collapse-btn"
        />
      </div>
      
      <template v-for="(route, index) in routes" :key="index">
        <el-menu-item v-if="!route.meta?.hidden && !route.children" :index="route.path">
          <el-icon v-if="route.meta?.icon"><component :is="route.meta.icon" /></el-icon>
          <template #title>{{ route.meta?.title }}</template>
        </el-menu-item>
      </template>
    </el-menu>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)

// 获取路由表中的路由
const routes = computed(() => {
  return router.options.routes.filter(route => !route.meta?.hidden && route.path !== '/')
})

// 当前激活的菜单
const activeMenu = computed(() => {
  return route.path
})

// 切换菜单折叠状态
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  overflow: hidden;
}

.el-menu-vertical {
  height: 100%;
  border-right: none;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 220px;
}

.menu-header {
  height: 50px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid #f0f0f0;
}

.collapse-btn {
  font-size: 18px;
  color: #909399;
}

.el-menu-item.is-active {
  background-color: #ecf5ff;
}

.el-menu-item:hover {
  background-color: #f5f7fa;
}
</style>