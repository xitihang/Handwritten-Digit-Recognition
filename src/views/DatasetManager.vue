<template>
  <div class="dataset-manager">
    <div class="header">
      <h1>数据集管理</h1>
      <div class="actions">
        <button class="btn-upload" @click="handleUpload">上传新数据集</button>
        <button class="btn-delete" @click="handleDelete">删除选中</button>
        <button class="btn-train" @click="handleSelectForTraining">用于训练</button>
      </div>
    </div>
    <div class="dataset-grid">
      <div class="dataset-card" v-for="dataset in datasets" :key="dataset.id">
        <h3>{{ dataset.name }}</h3>
        <p>{{ dataset.numImages }} 张图像 | {{ dataset.type }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getDatasets, addLog } from '@/services/api';

const datasets = ref([
  { id: 1, name: 'MNIST 基础数据集', numImages: 12000, type: '训练集' },
  { id: 2, name: 'EMNIST 扩展数据', numImages: 24500, type: '训练集' },
  { id: 3, name: 'Kuzushiji-MNIST', numImages: 8000, type: '验证集' },
  { id: 4, name: '自定义手写集', numImages: 3200, type: '测试集' },
  { id: 5, name: '增强版本 V1', numImages: 15000, type: '训练集' },
]);

const handleUpload = async () => {
  // TODO: 实现上传功能
  await addLog('上传新数据集');
  alert('上传功能待实现');
};

const handleDelete = async () => {
  // TODO: 实现删除功能
  await addLog('删除数据集');
  alert('删除功能待实现');
};

const handleSelectForTraining = async () => {
  // TODO: 实现选择数据集用于训练
  await addLog('选择数据集用于训练');
  alert('选择数据集功能待实现');
};

// onMounted(async () => {
//   try {
//     const response = await getDatasets();
//     datasets.value = response.data;
//   } catch (error) {
//     console.error('获取数据集失败:', error);
//   }
// });
</script>

<style scoped>
.dataset-manager {
  padding: 2rem;
  background-color: #f4f7f9;
  height: 100%;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

h1 {
  font-size: 1.8rem;
  font-weight: bold;
  color: #333;
}

.actions button {
  margin-left: 1rem;
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
}

.btn-upload {
  background-color: #e8f0fe;
  color: #1967d2;
  border: 1px solid #1967d2;
}

.btn-delete {
  background-color: #fce8e6;
  color: #d93025;
  border: 1px solid #d93025;
}

.btn-train {
  background-color: #1967d2;
  color: white;
}

.dataset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.5rem;
}

.dataset-card {
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}

.dataset-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-5px);
}

.dataset-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #333;
}

.dataset-card p {
  font-size: 0.9rem;
  color: #666;
}
</style>
