<template>
  <div class="model-manager">
    <div class="header">
      <h1>模型管理</h1>
    </div>
    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="loading" class="loading-message">加载中...</div>
    <div v-else-if="models.length === 0" class="empty-message">暂无模型</div>
    <div v-else class="model-list">
      <div class="model-card" v-for="model in models" :key="model.id" :class="{ active: model.active }">
        <div class="model-info">
          <h2>{{ model.name }}</h2>
          <p class="meta">
            <span class="user">训练用户: {{ model.user }}</span>
            <span class="time">训练时间: {{ model.trainTime }}分钟</span>
          </p>
          <p class="desc">{{ model.description }}</p>
        </div>
        <div class="model-stats">
          <div class="stat-item">
            <span class="value">{{ typeof model.accuracy === 'number' ? (model.accuracy * 100).toFixed(1) : model.accuracy }}%</span>
            <span class="label">准确率</span>
          </div>
          <div class="stat-item">
            <span class="value">{{ model.version }}</span>
            <span class="label">版本号</span>
          </div>
          <div class="stat-item">
            <span class="value">{{ model.trainDate }}</span>
            <span class="label">训练日期</span>
          </div>
        </div>
        <div class="model-actions">
          <button v-if="model.active" class="btn-in-use">正在使用</button>
          <button v-else-if="model.status === '未使用'" class="btn-apply" @click="applyModel(model.name)">应用模型</button>
           <button v-if="model.status === '未捷用'" class="btn-disabled" disabled>未捷用</button>
          <button class="btn-delete" @click="deleteModel(model.name)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getModels, applyModel as apiApplyModel, deleteModel as apiDeleteModel, addLog } from '@/services/api';

interface Model {
  id: string;
  name: string;
  user: string;
      trainTime: string | number; // ISO-8601 格式或分钟数
      accuracy: number | string; // 数字或百分比字符串
  version: string;
  trainDate: string; // ISO 日期时间字符串
  active: boolean;
  description?: string;
  status?: string;
}

const models = ref<Model[]>([]);
const loading = ref(false);
const error = ref('');

// 将 ISO-8601 时长转换为分钟数
const parseTrainTime = (timeStr: string): number => {
  if (!timeStr) return 0;
  // 简单解析，如 "PT2H30M" -> 150分钟
  const hoursMatch = timeStr.match(/(\d+)H/);
  const minutesMatch = timeStr.match(/(\d+)M/);
  const hours = hoursMatch ? parseInt(hoursMatch[1]) : 0;
  const minutes = minutesMatch ? parseInt(minutesMatch[1]) : 0;
  return hours * 60 + minutes;
};

// 格式化日期
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    return date.toISOString().split('T')[0];
  } catch {
    return dateStr.split('T')[0];
  }
};

const fetchModels = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await getModels();
    models.value = response.data.map((m: any) => ({
      ...m,
      trainTime: parseTrainTime(m.trainTime || ''),
      trainDate: formatDate(m.trainDate || ''),
      accuracy: m.accuracy, // 保持原值（后端返回的是 0-1 之间的数字）
      status: m.active ? '当前使用中' : '未使用',
      description: m.description || `${m.name} 模型`
    }));
  } catch (err: any) {
    console.error('获取模型列表失败:', err);
    error.value = '获取模型列表失败，请检查后端服务是否启动';
    models.value = [];
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchModels();
});

const applyModel = async (modelName: string) => {
  try {
    await apiApplyModel(modelName);
    // 更新本地状态
    models.value.forEach(m => {
      m.active = m.name === modelName;
      m.status = m.active ? '当前使用中' : '未使用';
    });
    // 记录日志
    await addLog(`应用模型: ${modelName}`);
    alert(`模型 ${modelName} 已成功应用`);
  } catch (err: any) {
    const errorMsg = err.response?.data?.error || err.message || '切换模型失败';
    alert(`切换模型失败: ${errorMsg}`);
    console.error(`切换模型 ${modelName} 失败:`, err);
    // 重新获取模型列表以同步状态
    await fetchModels();
  }
};

const deleteModel = async (modelName: string) => {
  if (!confirm(`确定要删除模型 ${modelName} 吗？`)) {
    return;
  }
  
  try {
    await apiDeleteModel(modelName);
    // 记录日志
    await addLog(`删除模型: ${modelName}`);
    alert(`模型 ${modelName} 已成功删除`);
    // 重新获取模型列表
    await fetchModels();
  } catch (err: any) {
    const errorMsg = err.response?.data?.error || err.message || '删除模型失败';
    alert(`删除模型失败: ${errorMsg}`);
    console.error(`删除模型 ${modelName} 失败:`, err);
  }
};
</script>

<style scoped>
.model-manager {
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

.model-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.model-card {
  display: grid;
  grid-template-columns: 2fr 3fr 1fr;
  align-items: center;
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem 2rem;
  transition: box-shadow 0.3s ease;
}

.model-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.model-card.active {
  border-left: 5px solid #34a853;
}

.model-info h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.model-info .meta {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.75rem;
}
.meta .user {
    margin-right: 1rem;
}

.model-info .desc {
  font-size: 0.9rem;
  color: #555;
}

.model-stats {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.stat-item {
  text-align: center;
}

.stat-item .value {
  display: block;
  font-size: 1.6rem;
  font-weight: 500;
  color: #333;
}

.stat-item .label {
  font-size: 0.85rem;
  color: #777;
}

.model-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.75rem;
}

.model-actions button {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  width: 120px;
  text-align: center;
}

.btn-in-use {
  background-color: #34a853;
  color: white;
}

.btn-apply {
  background-color: #1967d2;
  color: white;
}

.btn-disabled {
    background-color: #e0e0e0;
    color: #999;
    cursor: not-allowed;
}

.btn-delete {
    background-color: transparent;
    color: #d93025;
    border: 1px solid #d93025;
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
