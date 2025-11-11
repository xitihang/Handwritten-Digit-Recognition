import { io, Socket } from 'socket.io-client';

export interface TrainingProgress {
  epoch: number;
  train_loss: number;
  train_acc: number;
  val_loss?: number;
  val_acc?: number;
}

export interface TrainingComplete {
  model_path: string;
  final_train_acc: number;
  final_val_acc: number;
}

class TrainingSocketService {
  private socket: Socket | null = null;
  private isConnected = false;

  connect() {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io('http://localhost:5897', {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    this.socket.on('connect', () => {
      console.log('训练服务已连接');
      this.isConnected = true;
    });

    this.socket.on('disconnect', () => {
      console.log('训练服务已断开');
      this.isConnected = false;
    });

    this.socket.on('connect_error', (error) => {
      console.error('训练服务连接失败:', error);
      this.isConnected = false;
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
    }
  }

  startTraining(config: {
    model_architecture: string;
    dataset_name: string;
    save_model_name?: string;
    batch_size: number;
    learning_rate: number;
    epochs?: number;
    optimizer: string;
    loss_function: string;
  }) {
    if (!this.socket || !this.isConnected) {
      throw new Error('训练服务未连接，请确保 Python 后端已启动');
    }

    // 参数映射：前端 -> Python 后端
    const trainingRequest = {
      model_architecture: config.model_architecture === 'CNN' ? 'cnn_model' : 'mlp_model',
      dataset_name: config.dataset_name || 'mnist',
      save_model_name: config.save_model_name || `${config.model_architecture.toLowerCase()}_${Date.now()}`,
      batch_size: config.batch_size,
      learning_rate: config.learning_rate,
      epochs: config.epochs || 50,
      optimizer: config.optimizer.toLowerCase(),
      loss_function: config.loss_function === '交叉熵' ? 'cross_entropy' : config.loss_function.toLowerCase(),
    };

    this.socket.emit('start_training', trainingRequest);
  }

  stopTraining() {
    if (!this.socket || !this.isConnected) {
      throw new Error('训练服务未连接');
    }
    this.socket.emit('stop_training');
  }

  onTrainingStarted(callback: (data: { training_id: string }) => void) {
    this.socket?.on('training_started', callback);
  }

  onTrainingProgress(callback: (data: TrainingProgress) => void) {
    this.socket?.on('training_progress', callback);
  }

  onTrainingComplete(callback: (data: TrainingComplete) => void) {
    this.socket?.on('training_complete', callback);
  }

  onTrainingError(callback: (error: string) => void) {
    this.socket?.on('training_error', callback);
  }

  onTrainingStopped(callback: (message: string) => void) {
    this.socket?.on('training_stopped', callback);
  }

  off(event: string, callback?: (...args: any[]) => void) {
    if (callback) {
      this.socket?.off(event, callback);
    } else {
      this.socket?.off(event);
    }
  }

  getConnected(): boolean {
    return this.isConnected;
  }
}

export const trainingSocket = new TrainingSocketService();

