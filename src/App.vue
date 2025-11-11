<template>
  <!-- Layout with sidebar for all pages except login -->
  <div v-if="showSidebar" id="app-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1>手写数字识别</h1>
      </div>
      <nav class="sidebar-nav">
        <RouterLink to="/datasets">
          <i class="icon">📊</i> 数据集管理
        </RouterLink>
        <RouterLink to="/training">
          <i class="icon">🏋️</i> 训练管理
        </RouterLink>
        <RouterLink to="/models">
          <i class="icon">🤖</i> 模型管理
        </RouterLink>
        <RouterLink to="/logs">
          <i class="icon">📜</i> 日志管理
        </RouterLink>
      </nav>
    </aside>
    <main class="main-content">
      <RouterView />
    </main>
  </div>

  <!-- Full-screen layout for the login page -->
  <div v-else class="fullscreen-layout">
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, RouterView, useRoute } from 'vue-router';

const route = useRoute();
const showSidebar = computed(() => route.name !== 'login');
</script>

<style scoped>
#app-layout {
  display: flex;
  height: 100vh;
  background-color: #f4f7f9;
}

.fullscreen-layout {
  height: 100%;
  width: 100%;
}

.sidebar {
  width: 240px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 1.5rem;
  text-align: center;
  border-bottom: 1px solid #34495e;
}

.sidebar-header h1 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 600;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding-top: 1rem;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  padding: 0.9rem 1.5rem;
  color: #bdc3c7;
  text-decoration: none;
  font-size: 1rem;
  transition: background-color 0.3s, color 0.3s;
}

.sidebar-nav a .icon {
  margin-right: 0.8rem;
  font-style: normal;
}

.sidebar-nav a:hover {
  background-color: #34495e;
  color: white;
}

.sidebar-nav a.router-link-exact-active {
  background-color: #1abc9c;
  color: white;
  font-weight: 500;
}

.main-content {
  flex-grow: 1;
  overflow-y: auto;
}
</style>
