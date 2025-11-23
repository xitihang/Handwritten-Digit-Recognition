"""
移动端预测API服务
提供手写数字识别的HTTP接口，供微信小程序调用

主要功能：
1. 接收图片上传（multipart/form-data）
2. 图片预处理（resize到28x28，转灰度图，归一化）
3. 加载训练好的模型
4. 进行预测
5. 返回JSON结果：{"digit": "5", "confidence": 0.98, "probabilities": [...]}

API端点：
- POST /api/predict - 上传图片进行预测
- GET /api/health - 健康检查
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2

# 动态添加项目根目录到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.config_manager import ConfigManager
from core.predictor import Predictor

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求（微信小程序需要）

# 全局变量：预测器实例
predictor = None


def load_predictor():
    """
    初始化预测器
    从配置中读取模型并加载
    """
    global predictor
    
    try:
        config_manager = ConfigManager()
        predictor = Predictor(config_manager)
        predictor.load_model()
        
    except Exception as e:
        print(f"[ERROR] 预测器加载失败: {str(e)}")


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    predictor_ready = predictor is not None and predictor.is_ready()
    return jsonify({
        'status': 'ok',
        'predictor_ready': predictor_ready,
        'device': str(predictor.device) if predictor else 'unknown'
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    预测接口
    
    接收参数：
    - image: 图片文件（multipart/form-data）
    
    返回：
    {
        "success": true,
        "digit": "12345",
        "confidence": 0.98,
        "probabilities": [...]
    }
    """
    try:
        # 检查是否有图片上传
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传图片，请在请求中包含image字段'
            }), 400
        
        file = request.files['image']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '文件名为空'
            }), 400
        
        # 读取图片内容并转换为OpenCV格式
        file_bytes = file.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_np is None:
            return jsonify({
                'success': False,
                'error': '无法解析图片文件'
            }), 400
        
        if predictor is None:
            return jsonify({
                'success': False,
                'error': '预测器未初始化'
            }), 500

        # 预测
        result = predictor.predict(img_np)
        
        # 返回结果
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        print(f"[ERROR] 预测失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/model/info', methods=['GET'])
def model_info():
    """获取当前加载的模型信息"""
    try:
        if predictor is None:
            return jsonify({
                'success': False,
                'error': '预测器未初始化'
            }), 500
            
        model_info = predictor.get_model_info()
        
        return jsonify({
            'success': True,
            **model_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 启动服务 ====================

if __name__ == '__main__':
    print("[INFO] 初始化预测器...")
    load_predictor()
    
    print(f"[INFO] 服务启动 - http://localhost:5000/api/predict")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
