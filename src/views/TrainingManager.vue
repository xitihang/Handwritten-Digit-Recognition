<template>
  <div class="training-manager">
    <!-- 数据集设置 -->
    <div class="section-card dataset-setting">
      <div class="info">
        <h2>{{ datasetInfo.name }}</h2>
        <p>{{ datasetInfo.trainSize + datasetInfo.testSize }} 张图像 ({{ datasetInfo.trainSize }}k 训练集 + {{ datasetInfo.testSize / 1000 }}k 测试集) · {{ datasetInfo.imageSize }} 像素灰度图</p>
      </div>
      <button class="btn-switch">更换数据集</button>
    </div>

    <div class="main-content">
      <!-- 左侧配置区域 -->
      <div class="config-panel">
        <!-- 模型架构 -->
        <div class="section-card model-architecture">
          <h3>模型架构</h3>
          <div class="radio-group">
            <div class="radio-item" v-for="arch in architectures" :key="arch.name">
              <input type="radio" :id="arch.name" name="architecture" :value="arch.name" v-model="trainingConfig.modelType">
              <label :for="arch.name">
                <div class="arch-image">
                  <img :src="arch.name === 'CNN' ? '/src/assets/cnn-arch.png' : '/src/assets/mlp-arch.png'" :alt="arch.name">
                </div>
                <strong>{{ arch.name }}</strong>
                <span>{{ arch.desc }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 训练参数 -->
        <div class="section-card training-params">
          <h3>训练参数</h3>
          <div class="param-item">
            <label>学习率 (Learning Rate)</label>
            <div class="lr-slider">
              <span>{{ trainingConfig.lr.toFixed(4) }}</span>
              <input type="range" min="0.0001" max="0.1" step="0.0001" v-model.number="trainingConfig.lr">
              <div class="range-labels">
                <span>0.0001</span>
                <span>0.1000</span>
              </div>
            </div>
          </div>
          <div class="param-grid">
            <div class="param-item">
              <label>批处理大小 (Batch Size)</label>
              <input type="number" v-model.number="trainingConfig.batchSize">
              <small>推荐 32-128 之间</small>
            </div>
            <div class="param-item">
              <label>优化器</label>
              <select v-model="trainingConfig.optimizer">
                <option>Adam</option>
                <option>SGD</option>
                <option>RMSprop</option>
              </select>
            </div>
             <div class="param-item">
              <label>损失函数</label>
              <select v-model="trainingConfig.lossFunc">
                <option>交叉熵</option>
                <option>MSE</option>
              </select>
            </div>
          </div>
        </div>
         <div class="controls">
            <div class="connection-status" :class="connectionStatus">
              <span v-if="connectionStatus === 'connected'">● 已连接</span>
              <span v-else-if="connectionStatus === 'connecting'">● 连接中...</span>
              <span v-else>● 未连接</span>
            </div>
            <button class="btn-start" @click="startTrain" :disabled="!trainingSocket.getConnected() || isTraining">
              <i class="icon-play"></i> {{ isTraining ? '训练中...' : '开始训练' }}
            </button>
            <button class="btn-stop" @click="stopTrain" :disabled="!isTraining">停止训练</button>
          </div>
      </div>

      <!-- 右侧日志与可视化 -->
      <div class="log-visualization">
        <div class="section-card training-log">
           <div class="log-header">
            <h3>训练日志</h3>
            <button class="btn-fullscreen">⤢</button>
          </div>
          <div class="log-content">
            <p v-for="(log, index) in trainLogs" :key="index" :class="log.type">{{ log.message }}</p>
            <p v-if="trainLogs.length === 0" class="info">等待训练开始...</p>
          </div>
        </div>
        <div class="section-card training-visualization">
           <h3>训练过程可视化</h3>
           <div class="charts-container">
              <div class="chart">
                <h4>损失变化曲线 (Loss)</h4>
                <div class="chart-canvas">
                  <Line v-if="lossCurveData.length > 0" :key="`loss-${lossCurveData.length}`" :data="lossData" :options="lossOptions" />
                  <div v-else class="chart-empty">
                    <p>等待训练数据...</p>
                    <p class="hint">训练开始后，损失曲线将在这里显示</p>
                  </div>
                </div>
              </div>
              <div class="chart">
                <h4>准确率变化曲线 (Accuracy)</h4>
                <div class="chart-canvas">
                  <Line v-if="accCurveData.length > 0" :key="`acc-${accCurveData.length}`" :data="accData" :options="accOptions" />
                  <div v-else class="chart-empty">
                    <p>等待训练数据...</p>
                    <p class="hint">训练开始后，准确率曲线将在这里显示</p>
                  </div>
                </div>
              </div>
           </div>
           <div class="viz-controls">
             <button>暂停</button>
             <button>重新绘图</button>
             <select>
               <option>数据间隔: 每10个batch</option>
             </select>
           </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import {
  getTrainDataset,
  getArchitectures,
  getTrainConfig,
  startTraining,
  stopTraining,
  getTrainLogs,
  getTrainCurve,
  getTrainingLogs,
  addLog as addSystemLog,
} from '@/services/api';
import { trainingSocket, type TrainingProgress, type TrainingComplete } from '@/services/trainingSocket';
import { Line } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale } from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale);

// --- 响应式状态 ---

const datasetInfo = ref({
  name: 'MNIST 手写数字数据集',
  trainSize: 60000,
  testSize: 10000,
  imageSize: '28x28',
});

const architectures = ref([
    { name: 'CNN', desc: '2个卷积层 + 池化层 + 全连接层', image: '@/assets/cnn-arch.png' },
    { name: 'MLP', desc: '3层全连接网络', image: '@/assets/mlp-arch.png' }
]);

const trainingConfig = ref({
  modelType: 'CNN',
  lr: 0.01,
  batchSize: 64,
  optimizer: 'Adam',
  lossFunc: '交叉熵',
});

const trainLogs = ref<Array<{ type: string; message: string }>>([]);
const lossCurveData = ref<number[]>([]);
const accCurveData = ref<number[]>([]);
const isTraining = ref(false);
const connectionStatus = ref<'connected' | 'disconnected' | 'connecting'>('disconnected');

// 连接状态检查定时器
let checkConnection: ReturnType<typeof setInterval> | null = null;


// --- WebSocket 事件处理 ---

const addLog = (type: string, message: string) => {
  trainLogs.value.push({ type, message });
  // 限制日志数量，避免内存溢出
  if (trainLogs.value.length > 1000) {
    trainLogs.value = trainLogs.value.slice(-500);
  }
};

const handleTrainingStarted = (data: { training_id: string }) => {
  isTraining.value = true;
  trainLogs.value = [];
  lossCurveData.value = [];
  accCurveData.value = [];
  addLog('info', `[INFO] 训练任务已启动 (ID: ${data.training_id})`);
  addLog('info', `[CONFIG] 模型架构: ${trainingConfig.value.modelType}`);
  addLog('info', `[CONFIG] 优化器: ${trainingConfig.value.optimizer} (lr=${trainingConfig.value.lr})`);
  addLog('info', `[CONFIG] 批处理大小: ${trainingConfig.value.batchSize}`);
  // 记录系统日志
  addSystemLog(`启动训练任务: ${trainingConfig.value.modelType} (ID: ${data.training_id})`);
};

const handleTrainingProgress = (data: TrainingProgress) => {
  const epoch = data.epoch;
  const trainLoss = data.train_loss;
  const trainAcc = data.train_acc * 100; // 转换为百分比
  const valLoss = data.val_loss;
  const valAcc = data.val_acc ? data.val_acc * 100 : undefined;

  // 添加日志
  addLog('epoch', `[EPOCH ${epoch}] 训练损失: ${trainLoss.toFixed(4)} | 训练准确率: ${trainAcc.toFixed(2)}%`);
  if (valLoss !== undefined && valAcc !== undefined) {
    addLog('validation', `[VALIDATION] 验证损失: ${valLoss.toFixed(4)} | 验证准确率: ${valAcc.toFixed(2)}%`);
  }

  // 更新曲线数据
  lossCurveData.value.push(trainLoss);
  if (valLoss !== undefined) {
    // 可以同时显示训练和验证损失
  }
  accCurveData.value.push(trainAcc);
  if (valAcc !== undefined) {
    // 可以同时显示训练和验证准确率
  }
};

const handleTrainingComplete = (data: TrainingComplete) => {
  isTraining.value = false;
  addLog('info', `[INFO] 训练完成！`);
  addLog('info', `[RESULT] 最终训练准确率: ${(data.final_train_acc * 100).toFixed(2)}%`);
  addLog('info', `[RESULT] 最终验证准确率: ${(data.final_val_acc * 100).toFixed(2)}%`);
  addLog('info', `[RESULT] 模型保存路径: ${data.model_path}`);
  // 记录系统日志
  addSystemLog(`训练完成: 训练准确率 ${(data.final_train_acc * 100).toFixed(2)}%, 验证准确率 ${(data.final_val_acc * 100).toFixed(2)}%`);
  alert('训练完成！');
};

const handleTrainingError = (error: string) => {
  isTraining.value = false;
  addLog('error', `[ERROR] ${error}`);
  alert(`训练出错: ${error}`);
};

const handleTrainingStopped = (message: string) => {
  isTraining.value = false;
  addLog('info', `[INFO] ${message}`);
  // 记录系统日志
  addSystemLog(`停止训练任务`);
  alert(message);
};

// --- API 调用 ---

const loadHistoryData = async () => {
  try {
    const logsRes = await getTrainingLogs();
    if (logsRes.data.logs && logsRes.data.logs.length > 0) {
      // 从历史日志加载数据到图表
      const logs = logsRes.data.logs;
      lossCurveData.value = logs.map((log: any) => log.train_loss);
      accCurveData.value = logs.map((log: any) => log.train_acc * 100);
      
      // 添加历史日志到日志列表（只显示最后50条，避免太多）
      const recentLogs = logs.slice(-50);
      recentLogs.forEach((log: any) => {
        addLog('epoch', `[EPOCH ${log.epoch}] 训练损失: ${log.train_loss.toFixed(4)} | 训练准确率: ${(log.train_acc * 100).toFixed(2)}%`);
        if (log.val_loss !== undefined && log.val_acc !== undefined) {
          addLog('validation', `[VALIDATION] 验证损失: ${log.val_loss.toFixed(4)} | 验证准确率: ${(log.val_acc * 100).toFixed(2)}%`);
        }
      });
      
      if (logs.length > 50) {
        addLog('info', `[INFO] 已加载历史训练日志: ${logsRes.data.log_file} (共 ${logs.length} 个epoch，显示最后50个)`);
      } else {
        addLog('info', `[INFO] 已加载历史训练日志: ${logsRes.data.log_file} (共 ${logs.length} 个epoch)`);
      }
    }
  } catch (error: any) {
    console.error('加载历史训练日志失败:', error);
    const errorMsg = error.response?.data?.error || error.message || '未知错误';
    if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error') || error.message?.includes('Failed to fetch')) {
      addLog('error', `[ERROR] 无法连接到训练服务器 (http://localhost:5897)`);
      addLog('error', `[ERROR] 请确保 Python 服务器已启动: cd handwriting_recognition_system/web && python web_server.py`);
    } else {
      addLog('error', `[ERROR] 加载历史日志失败: ${errorMsg}`);
    }
  }
};

onMounted(async () => {
  // 连接 WebSocket
  connectionStatus.value = 'connecting';
  trainingSocket.connect();

  // 设置事件监听器
  trainingSocket.onTrainingStarted(handleTrainingStarted);
  trainingSocket.onTrainingProgress(handleTrainingProgress);
  trainingSocket.onTrainingComplete(handleTrainingComplete);
  trainingSocket.onTrainingError(handleTrainingError);
  trainingSocket.onTrainingStopped(handleTrainingStopped);

  // 监听连接状态
  checkConnection = setInterval(() => {
    if (trainingSocket.getConnected()) {
      connectionStatus.value = 'connected';
    } else {
      connectionStatus.value = 'disconnected';
    }
  }, 1000);

  // 尝试加载历史训练数据
  loadHistoryData();
});

onUnmounted(() => {
  // 清理定时器
  if (checkConnection) {
    clearInterval(checkConnection);
  }
  
  // 移除事件监听器
  trainingSocket.off('training_started', handleTrainingStarted);
  trainingSocket.off('training_progress', handleTrainingProgress);
  trainingSocket.off('training_complete', handleTrainingComplete);
  trainingSocket.off('training_error', handleTrainingError);
  trainingSocket.off('training_stopped', handleTrainingStopped);
  
  // 断开连接
  trainingSocket.disconnect();
});

const startTrain = async () => {
  if (!trainingSocket.getConnected()) {
    alert('训练服务未连接，请确保 Python 后端已启动 (http://localhost:5897)');
    return;
  }

  if (isTraining.value) {
    alert('训练正在进行中，请先停止当前训练');
    return;
  }

  try {
    // 参数映射：前端 -> Python 后端
    trainingSocket.startTraining({
      model_architecture: trainingConfig.value.modelType,
      dataset_name: 'mnist', // 默认使用 MNIST
      batch_size: trainingConfig.value.batchSize,
      learning_rate: trainingConfig.value.lr,
      optimizer: trainingConfig.value.optimizer,
      loss_function: trainingConfig.value.lossFunc,
    });
  } catch (error: any) {
    console.error('启动训练失败:', error);
    alert(`启动训练失败: ${error.message}`);
  }
};

const stopTrain = async () => {
  if (!isTraining.value) {
    alert('当前没有正在进行的训练');
    return;
  }

  try {
    trainingSocket.stopTraining();
  } catch (error: any) {
    console.error('停止训练失败:', error);
    alert(`停止训练失败: ${error.message}`);
  }
};


// --- Chart.js 配置 ---

const lossYMax = computed(() => {
  if (lossCurveData.value.length === 0) return 1.2;
  return Math.max(1, ...lossCurveData.value) * 1.2;
})

const lossOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 0 }, // 避免首帧从基线拉一条很长的线
  scales: { y: { min: 0, max: lossYMax.value } },
  plugins: { legend: { display: false } }
}))

const accOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 0 },
  scales: { y: { min: 0, max: 100 } },
  plugins: { legend: { display: false } }
}

const lossData = computed(() => {
  // 如果数据为空，返回空图表结构
  if (lossCurveData.value.length === 0) {
    return {
      labels: [],
      datasets: [{
        label: 'Loss',
        data: [],
        borderColor: '#f87979',
        backgroundColor: 'rgba(248, 121, 121, 0.1)',
        borderWidth: 2,
        tension: 0.25,
        pointRadius: 3,
        showLine: false
      }]
    };
  }
  return {
    labels: lossCurveData.value.map((_, i) => `Epoch ${i + 1}`),
    datasets: [{
      label: 'Loss',
      data: lossCurveData.value,
      borderColor: '#f87979',
      backgroundColor: 'rgba(248, 121, 121, 0.1)',
      borderWidth: 2,
      tension: 0.25,
      pointRadius: 3,
      showLine: lossCurveData.value.length >= 2
    }]
  };
})

const accData = computed(() => {
  // 如果数据为空，返回空图表结构
  if (accCurveData.value.length === 0) {
    return {
      labels: [],
      datasets: [{
        label: 'Accuracy',
        data: [],
        borderColor: '#79f8a3',
        backgroundColor: 'rgba(121, 248, 163, 0.1)',
        borderWidth: 2,
        tension: 0.25,
        pointRadius: 3,
        showLine: false
      }]
    };
  }
  return {
    labels: accCurveData.value.map((_, i) => `Epoch ${i + 1}`),
    datasets: [{
      label: 'Accuracy',
      data: accCurveData.value,
      borderColor: '#79f8a3',
      backgroundColor: 'rgba(121, 248, 163, 0.1)',
      borderWidth: 2,
      tension: 0.25,
      pointRadius: 3,
      showLine: accCurveData.value.length >= 2
    }]
  };
})

</script>

<style scoped>
.training-manager {
  padding: 2rem;
  background-color: #f4f7f9;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.section-card {
  background-color: white;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  padding: 1.5rem;
}

.dataset-setting {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-shrink: 0; /* 防止此元素在 flex 布局中被压缩 */
}
.dataset-setting .info h2 {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  margin: 0 0 0.25rem 0;
}
.dataset-setting .info p {
  color: #666;
  margin: 0;
}
.btn-switch {
  padding: 0.7rem 1.5rem;
  background-color: #1967d2;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  flex-grow: 1; /* 占据剩余的垂直空间 */
  min-height: 0; /* 防止 grid 在 flex 布局中溢出 */
}

.config-panel .section-card, .log-visualization .section-card {
    margin-bottom: 1.5rem;
}
.config-panel .section-card:last-child {
    margin-bottom: 0;
}


.config-panel h3, .log-visualization h3 {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
}

/* 模型架构 */
.model-architecture .radio-group {
  display: flex;
  gap: 1rem;
}
.radio-item input[type="radio"] {
  display: none;
}
.radio-item label {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 180px;
}
.radio-item input[type="radio"]:checked + label {
  border-color: #1967d2;
  box-shadow: 0 0 10px rgba(25, 103, 210, 0.2);
}
.arch-image {
  width: 100%;
  height: 100px;
  margin-bottom: 1rem;
}
.arch-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.radio-item label strong {
  font-size: 1rem;
  font-weight: bold;
}
.radio-item label span {
  font-size: 0.8rem;
  color: #666;
  text-align: center;
}

/* 训练参数 */
.param-item {
  margin-bottom: 1.5rem;
}
.param-item label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
}
.lr-slider {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.lr-slider input[type="range"] {
  flex-grow: 1;
}
.lr-slider .range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #666;
  width: 100%;
  padding: 0 5px;
}
.param-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}
input[type="number"], select {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.param-item small {
  font-size: 0.8rem;
  color: #888;
  margin-top: 0.25rem;
}

/* 控制按钮 */
.controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1.5rem;
}
.connection-status {
  padding: 0.5rem 1rem;
  border-radius: 5px;
  font-size: 0.9rem;
  text-align: center;
}
.connection-status.connected {
  background-color: #d4edda;
  color: #155724;
}
.connection-status.connecting {
  background-color: #fff3cd;
  color: #856404;
}
.connection-status.disconnected {
  background-color: #f8d7da;
  color: #721c24;
}
.controls button {
  flex-grow: 1;
  padding: 0.8rem;
  font-size: 1rem;
  border-radius: 5px;
  border: none;
  cursor: pointer;
}
.controls button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-start {
  background-color: #34a853;
  color: white;
}
.btn-stop {
  background-color: #ea4335;
  color: white;
}

/* 日志与可视化 */
.log-visualization {
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.training-log {
    flex-grow: 1; /* 日志卡片占据所有可用空间 */
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}
.log-content {
  height: 100%; /* 填充 training-log 卡片的剩余空间 */
  background-color: #2d2d2d;
  color: #f1f1f1;
  padding: 1rem;
  border-radius: 5px;
  overflow-y: auto;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9rem;
  line-height: 1.6;
}
.log-content p { margin: 0; }
.log-content .info { color: #87cefa; }
.log-content .epoch { color: #ffd700; font-weight: bold; }
.log-content .step { color: #adff2f; }
.log-content .validation { color: #ff69b4; font-weight: bold; }

.training-visualization {
    flex-shrink: 0; /* 可视化卡片不被压缩 */
    margin-bottom: 0;
}

.charts-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.chart-canvas {
  height: 260px;
}

.chart-canvas canvas {
  width: 100% !important;
  height: 100% !important;
}

.chart-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #999;
  font-size: 0.9rem;
}

.chart-empty .hint {
  font-size: 0.8rem;
  color: #bbb;
  margin-top: 0.5rem;
}

.viz-controls {
  margin-top: 1rem;
  display: flex;
  gap: 1rem;
  align-items: center;
}
.viz-controls button, .viz-controls select {
  padding: 0.5rem 1rem;
  background: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 4px;
}
</style>
