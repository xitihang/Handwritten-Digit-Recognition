# 主要功能：
# 1. 接收"开始训练"信号：解析请求参数，创建训练配置，启动一个独立的进程运行Trainer.train()，并通过队列实时捕获训练进度日志并推送给客户端。
# 2. 接收"停止训练"信号：终止正在运行的训练进程（直接切断执行），并推送停止确认。
# 3. 实时推送训练信息：使用SocketIO事件（如'training_progress'）将Trainer的日志（每个epoch的loss/acc）推送给Java客户端。
# 4. 处理训练完成/错误：推送最终结果或错误信息。
#
# 与Java后端的交互结构设计（反向设计基于Trainer接口）：
# - 连接：Java客户端连接WebSocket (ws://localhost:5897)。
# - 开始训练：Java发送SocketIO事件 'start_training'，data为JSON对象，例如：
#   {
#     "model_architecture": "cnn_model",
#     "dataset_name": "mnist",
#     "save_model_name": "cnn_custom_001",
#     "batch_size": 64,
#     "learning_rate": 0.001,
#     "epochs": 50,
#     "optimizer": "adam",
#     "loss_function": "cross_entropy"
#   }
#   （这些参数对应Trainer所需的components和ConfigManager.create_training_config()的输入）
# - 停止训练：Java发送事件 'stop_training'（无data）。
# - 接收推送：
#   - 'training_started': {"training_id": "train_YYYYMMDD_HHMMSS"} （确认开始）
#   - 'training_progress': {"epoch": 1, "train_loss": 0.1234, "train_acc": 0.8765, "val_loss": 0.1111, "val_acc": 0.8888} （每个epoch推送一次，对应Trainer的progress_callback(log)）
#   - 'training_complete': {"model_path": "/path/to/model.pth", "final_train_acc": 0.95, "final_val_acc": 0.96} （训练结束，对应Trainer.train()返回值）
#   - 'training_error': "错误描述字符串" （异常时推送）
#   - 'training_stopped': "训练已停止" （停止确认）
# - 注意：进度推送基于Trainer的progress_callback接口，该接口在每个epoch后被调用，推送log dict。
#   Trainer的train()返回值用于完成事件；如果进程异常，捕获并推送错误。
#   停止使用进程终止（mp.Process.terminate()），直接切断Trainer执行，无需Trainer支持停止接口。
#
# 依赖：需安装 flask, flask-socketio, torch 等。
# 运行：python web_server.py，监听localhost:5897。

import os
import sys
import json
import multiprocessing as mp
from datetime import datetime
from flask import Flask, request
from flask_socketio import SocketIO, emit
from threading import Thread
import traceback


# FIXED: 动态添加项目根目录到 sys.path，确保从 web/ 目录运行时能导入 config/ 和 core/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # web/ 的上级，即 handwriting_recognition_system/
sys.path.insert(0, project_root)

# 导入项目模块
from config.config_manager import ConfigManager  # 用于创建/管理配置
from core.model_factory import ModelFactory  # 用于创建训练组件
from core.trainer import Trainer  # 训练器

app = Flask(__name__)
app.config['SECRET_KEY'] = 'handwriting_recognition_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')  # 支持跨域，线程模式以便多线程emit

# 全局变量：跟踪当前训练进程和队列
current_process = None
progress_queue = None
poller_thread = None

def run_training_process(training_config_path, queue):
    """
    训练进程的入口函数：在独立进程中运行Trainer.train()。
    - 使用队列发送进度/完成/错误消息。
    - progress_callback 将每个epoch的log放入队列。
    - 异常时放入错误消息。
    """
    try:
        # 加载配置（因为进程独立，需要路径传递）
        config_manager = ConfigManager()
        model_factory = ModelFactory(config_manager)
        
        # 获取训练配置
        training_config = config_manager.get_train_config()  # 从保存的JSON加载
        
        # 创建组件
        components = model_factory.create_training_components()
        
        def progress_callback(log):
            """Trainer的回调：将log放入队列，供主进程emit给Java。"""
            queue.put(('progress', log))
        
        trainer = Trainer(components, progress_callback)
        result = trainer.train()  # 阻塞执行训练
        queue.put(('complete', result))  # 训练完成，放入结果
    except Exception as e:
        error_msg = f"训练过程中发生错误: {str(e)}\n{traceback.format_exc()}"
        queue.put(('error', error_msg))

def start_progress_poller(queue, process):
    """
    进度轮询线程：监听队列，从中取出消息并通过SocketIO emit给客户端。
    - 持续运行直到进程结束。
    - 支持progress、complete、error消息。
    """
    global poller_thread
    while process.is_alive() or not queue.empty():
        try:
            msg_type, msg_data = queue.get(timeout=1)
            if msg_type == 'progress':
                emit('training_progress', msg_data)
                socketio.sleep(0)  # FIXED: 增强 emit 异步
            elif msg_type == 'complete':
                emit('training_complete', msg_data)
                break
            elif msg_type == 'error':
                emit('training_error', msg_data)
                break
        except mp.queues.Empty:
            continue
    poller_thread = None

@socketio.on('start_training')
def handle_start_training(data):
    """
    处理开始训练事件。
    - 解析data（训练请求参数）。
    - 创建并保存训练配置。
    - 启动进程和轮询线程。
    - 推送开始确认。
    """
    global current_process, progress_queue, poller_thread
    
    if current_process and current_process.is_alive():
        emit('training_error', '已有训练正在进行中，请先停止。')
        return
    
    try:
        # 创建配置管理器
        config_manager = ConfigManager()
        
        # 根据请求创建训练配置（使用ConfigManager的接口）
        training_config = config_manager.create_training_config(data)
        
        # 保存训练配置到文件（Trainer需要从文件加载）
        config_manager._save_json(config_manager.train_config_path, training_config)
        
        # 创建队列用于进程间通信
        progress_queue = mp.Queue()
        
        # 启动训练进程（传递配置路径）
        current_process = mp.Process(
            target=run_training_process,
            args=(config_manager.train_config_path, progress_queue)
        )
        current_process.start()
        
        # 启动轮询线程监听队列
        poller_thread = Thread(target=start_progress_poller, args=(progress_queue, current_process))
        poller_thread.start()
        
        # 推送开始事件
        emit('training_started', {'training_id': training_config['training_id']})
        
    except Exception as e:
        error_msg = f"启动训练失败: {str(e)}"
        emit('training_error', error_msg)

@socketio.on('stop_training')
def handle_stop_training():
    """
    处理停止训练事件。
    - 如果进程存在且运行中，终止进程（直接切断Trainer执行）。
    - 清空队列，停止轮询。
    - 推送停止确认。
    """
    global current_process, progress_queue, poller_thread
    
    if current_process and current_process.is_alive():
        current_process.terminate()  # 强制终止进程（切断Trainer.train()）
        current_process.join(timeout=2)  # 等待短暂时间
        if current_process.is_alive():
            current_process.kill()  # 如果仍存活，强制杀死
        current_process = None
        
        # 清空队列和停止轮询
        while not progress_queue.empty():
            progress_queue.get_nowait()
        if poller_thread:
            poller_thread.join(timeout=1)
    
    emit('training_stopped', '训练已停止')

@app.route('/health')
def health_check():
    """简单健康检查端点（Java可调用确认服务器运行）。"""
    is_training = current_process.is_alive() if current_process is not None else False
    return {'status': 'ok', 'current_training': is_training}

if __name__ == '__main__':
    # 确保配置目录存在
    config_manager = ConfigManager()
    config_manager._ensure_config_files_exist()
    
    # 运行服务器
    socketio.run(app, host='localhost', port=5897, debug=True)