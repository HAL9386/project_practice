<template>
  <div class="app-container">
    <el-container>
      <el-header height="60px">
        <app-header />
      </el-header>
      <el-container>
        <el-aside width="220px">
          <app-sidebar />
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import AppHeader from './components/layout/AppHeader.vue'
import AppSidebar from './components/layout/AppSidebar.vue'
</script>

<style scoped>
.app-container {
  height: 100vh;
  width: 100%;
}

.el-header {
  background-color: #1e88e5;
  color: white;
  padding: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);
  position: relative;
  z-index: 10;
}

.el-aside {
  background-color: #ffffff;
  border-right: 1px solid #e6e6e6;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.el-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>