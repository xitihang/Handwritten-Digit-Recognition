<template>
  <div class="log-viewer">
    <div class="header">
      <h1>系统操作日志</h1>
    </div>
    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="loading" class="loading-message">加载中...</div>
    <div v-else class="log-table-container">
      <table class="log-table" v-if="logs.length > 0">
        <thead>
          <tr>
            <th>操作用户名</th>
            <th>操作内容</th>
            <th>操作时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(log, index) in logs" :key="index">
            <td>{{ log.user }}</td>
            <td>
              <span :class="getActionClass(log.action)">{{ log.action }}</span>
            </td>
            <td>{{ log.time }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-message">暂无日志记录</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { getLogs } from '@/services/api';

const logs = ref<Array<{ user: string; action: string; time: string }>>([]);
const loading = ref(false);
const error = ref('');
let refreshInterval: ReturnType<typeof setInterval> | null = null;

onMounted(async () => {
  await fetchLogs();
  // 每5秒自动刷新日志
  refreshInterval = setInterval(async () => {
    await fetchLogs();
  }, 5000);
});

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});

const fetchLogs = async () => {
  // 只在首次加载时显示 loading
  if (logs.value.length === 0) {
    loading.value = true;
  }
  error.value = '';
  try {
    const response = await getLogs();
    // 反转数组，使最新的日志显示在最上面
    logs.value = [...response.data].reverse();
  } catch (err) {
    console.error('获取日志失败:', err);
    error.value = '获取日志失败，请检查后端服务是否启动';
    // 如果后端未启动，使用空数组而不是模拟数据
    logs.value = [];
  } finally {
    loading.value = false;
  }
};

const getActionClass = (action: string) => {
  if (action.includes('删除') || action.includes('过时')) {
    return 'action-delete';
  }
  if (action.includes('上传') || action.includes('发布')) {
    return 'action-upload';
  }
  if (action.includes('登录') || action.includes('启动')) {
    return 'action-important';
  }
  return '';
};
</script>

<style scoped>
.log-viewer {
  padding: 2rem;
  background-color: #f4f7f9;
  height: 100%;
}

.header h1 {
  font-size: 1.8rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 2rem;
}

.log-table-container {
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.log-table {
  width: 100%;
  border-collapse: collapse;
}

.log-table th,
.log-table td {
  padding: 1rem 1.5rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.log-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
}

.log-table tbody tr:last-child td {
  border-bottom: none;
}

.log-table tbody tr:hover {
  background-color: #f1f3f5;
}

.log-table td {
  color: #555;
  font-size: 0.95rem;
}

.action-delete {
  color: #d93025;
  font-weight: 500;
}

.action-upload {
  color: #1e8e3e;
  font-weight: 500;
}

.action-important {
  color: #1967d2;
  font-weight: 500;
}

.error-message {
  background-color: #fce8e6;
  color: #d93025;
  border: 1px solid #d93025;
  border-radius: 5px;
  padding: 1rem;
  margin-bottom: 1rem;
  text-align: center;
}

.loading-message {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.empty-message {
  text-align: center;
  padding: 3rem;
  color: #999;
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}
</style>
