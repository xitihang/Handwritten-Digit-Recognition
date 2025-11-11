import axios from 'axios';

// 认证服务 API 客户端（端口 8080）
const authApiClient = axios.create({
  baseURL: 'http://localhost:8080/api',
  headers: {
    'Content-Type': 'application/json',
  },
  // 支持携带 cookies（用于 Session 管理）
  withCredentials: true,
});

// 日志服务 API 客户端（端口 8081）
const logApiClient = axios.create({
  baseURL: 'http://localhost:8081/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// 模型管理服务 API 客户端（端口 8082）
const modelApiClient = axios.create({
  baseURL: 'http://localhost:8082/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// 通用 API 客户端（默认端口 8080，用于其他服务）
const apiClient = axios.create({
  baseURL: 'http://localhost:8080/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// --- 认证 API（端口 8080）---
// 获取验证码图片
export const getCaptcha = () => authApiClient.get('/auth/getVerifyCodeImg');

// 用户登录
export const login = (userid: number, password: string, verifyCode: string, verifyCodeId: string) => 
  authApiClient.post('/auth/login', { 
    userid, 
    password, 
    verifyCode, 
    verifyCodeId,
    clientInfo: {
      os: navigator.platform,
      browser: navigator.userAgent,
      loginIp: ''
    }
  });

// 获取当前用户信息
export const getCurrentUser = () => authApiClient.get('/auth/currentUser');

// 退出登录
export const logout = () => authApiClient.post('/auth/logout');

// --- 数据集管理 API ---

// 获取所有数据集
export const getDatasets = () => apiClient.get('/datasets');

// 删除数据集
export const deleteDataset = (datasetName: string) => apiClient.delete(`/datasets/${datasetName}`);

// 选择数据集用于训练
export const selectDataset = (datasetName: string) => apiClient.post('/datasets/select', { datasetName });


// --- 模型管理 API（端口 8082）---

// 获取所有模型列表
export const getModels = () => modelApiClient.get('/models');

// 切换当前模型
export const applyModel = (modelName: string) => modelApiClient.post('/models/apply', { modelName });

// 删除模型
export const deleteModel = (modelName: string) => modelApiClient.delete(`/models/${modelName}`);


// --- 日志管理 API（端口 8081）---

// 获取日志列表
export const getLogs = () => logApiClient.get('/logs');

// 写入日志（自动获取当前用户）
export const addLog = async (action: string) => {
  const userId = localStorage.getItem('userId') || 'unknown';
  const now = new Date();
  const time = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
  try {
    await logApiClient.post('/logs', { user: `用户${userId}`, action, time });
  } catch (err) {
    // 静默失败，不影响主流程
    console.warn('记录日志失败:', err);
  }
};


// --- 训练管理 API ---

// 获取当前数据集信息
export const getTrainDataset = () => apiClient.get('/train/dataset');

// 获取可选模型架构
export const getArchitectures = () => apiClient.get('/train/architectures');

// 获取当前训练参数
export const getTrainConfig = () => apiClient.get('/train/config');

// 设置训练参数
export const setTrainConfig = (config: any) => apiClient.post('/train/config', config);

// 启动训练
export const startTraining = (config: any) => apiClient.post('/train/start', config);

// 停止训练
export const stopTraining = () => apiClient.post('/train/stop');

// 获取训练日志（长轮询或 WebSocket 更佳，此处为示例）
export const getTrainLogs = () => apiClient.get('/train/logs');

// 获取训练曲线数据
export const getTrainCurve = () => apiClient.get('/train/curve');

// --- Python 训练服务 API（端口 5897）---

// 获取历史训练日志
export const getTrainingLogs = () => {
  const trainingApiClient = axios.create({
    baseURL: 'http://localhost:5897',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return trainingApiClient.get('/api/training-logs');
};
