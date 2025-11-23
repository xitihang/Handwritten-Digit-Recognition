import sys
import os

# 添加项目根目录到 sys.path，以便能够导入 core 模块
# 假设当前文件在 core/ 目录下，项目根目录是上一级
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import cv2
import numpy as np
import torch
from torchvision import transforms
from core.model_factory import ModelFactory

class Predictor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # 转换器：OpenCV图片(numpy) -> PIL -> Gray -> Resize -> Tensor
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Grayscale(),
            transforms.Resize((28, 28)),
            transforms.ToTensor(),
        ])
        self.index_to_class = [str(i) for i in range(10)]

    def load_model(self):
        """加载模型"""
        factory = ModelFactory(self.config_manager)
        
        # 1. 从配置中获取模型架构名称
        model_name = self.config_manager.get_mobile_prediction_model()
        print(f"使用模型架构: {model_name}")
        
        # 2. 创建模型实例
        self.model = factory.create_model(model_name)
        
        # 3. 从配置中获取权重路径
        weights_path_relative = self.config_manager.get_prediction_weights_path()
        
        if weights_path_relative:
            # 构建绝对路径
            project_root = self.config_manager.config_dir.parent
            weights_path = os.path.join(project_root, weights_path_relative)
            
            if os.path.exists(weights_path):
                try:
                    self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
                    print(f"已加载预训练权重: {weights_path}")
                except Exception as e:
                    print(f"加载权重失败: {e}")
            else:
                print(f"警告: 权重文件不存在: {weights_path}")
        else:
            print("警告: 未配置预训练权重路径 (model_weights_path)")

        self.model.to(self.device)
        self.model.eval()

    def is_ready(self):
        return self.model is not None

    def get_model_info(self):
        if self.model:
            return {
                "device": str(self.device),
                "model_type": type(self.model).__name__
            }
        return {}

    def _pre_processing(self, img):
        """
        图片预处理：灰度 -> 二值化 -> 确保黑底白字
        目的：生成适合轮廓检测和模型输入的二值化图像（实心数字）
        """
        # 1. 转灰度
        if len(img.shape) == 3:
            imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            imgGray = img

        # 2. 高斯模糊去噪
        imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
        
        # 3. 二值化 (使用OTSU自动寻找最佳阈值)
        # cv2.THRESH_BINARY_INV 假设原图是白底黑字，将其转为黑底白字
        _, imgThres = cv2.threshold(imgBlur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 4. 智能背景检测与反转
        # 神经网络通常需要黑底白字。
        # 我们检查图像边缘的像素，如果边缘大部分是白色，说明当前是白底黑字，需要反转。
        h, w = imgThres.shape
        # 取四个角的像素值
        corners = [imgThres[0, 0], imgThres[0, w-1], imgThres[h-1, 0], imgThres[h-1, w-1]]
        # 统计白色角的数量
        white_corners = sum([1 for c in corners if c > 127])
        
        if white_corners > 2: 
            # 如果大部分角是白色的，说明背景是白的（即当前图像是白底黑字），反转为黑底白字
            imgThres = cv2.bitwise_not(imgThres)

        # 5. 形态学操作：轻微膨胀以连接断开的笔画，并填充细微空洞
        kernel = np.ones((3, 3), np.uint8)
        imgDial = cv2.dilate(imgThres, kernel, iterations=1)
        
        return imgDial

    def _get_contours(self, img_process):
        """轮廓检测与字符分割"""
        border_list = []
        # 检索外部轮廓
        contours, _ = cv2.findContours(img_process, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 50:  # 面积阈值，可根据实际情况调整
                # 计算周长
                peri = cv2.arcLength(cnt, True)
                # 计算拐角
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                # 得到外接矩形
                x, y, w, h = cv2.boundingRect(approx)
                
                dd = abs((w - h) // 2)
                # 从预处理后的图中切出字符
                img_get = img_process[y:y + h, x:x + w]
                
                try:
                    # 补成正方形并留黑边
                    if w <= h:  # 高度大于宽度，左右补黑边
                        img_get = cv2.copyMakeBorder(img_get, 20, 20, 20 + dd, 20 + dd, cv2.BORDER_CONSTANT, value=[0, 0, 0])
                        xx = x - dd - 10
                        yy = y - 10
                        ss = h + 20
                    else:  # 宽度大于高度，上下补黑边
                        img_get = cv2.copyMakeBorder(img_get, 20 + dd, 20 + dd, 20, 20, cv2.BORDER_CONSTANT, value=[0, 0, 0])
                        xx = x - 10
                        yy = y - dd - 10
                        ss = w + 20
                    
                    border_list.append((img_get, xx, yy, ss))
                except Exception as e:
                    print(f"Error processing contour: {e}")
                    continue

        # 按 x 坐标排序 (从左到右)
        border_list.sort(key=lambda x: x[1])
        return border_list

    def predict(self, img_original):
        """
        执行多数字识别
        Args:
            img_original: OpenCV格式的原始图片 (BGR)
        Returns:
            dict: 包含识别结果字符串和置信度
        """
        if self.model is None:
            raise Exception("Model not initialized")

        # 1. 预处理
        img_process = self._pre_processing(img_original)
        
        # 2. 获取轮廓和分割后的图片
        border_list = self._get_contours(img_process)
        
        results = []
        confidences = []
        
        # 用于显示的图片副本
        img_display = img_original.copy()
        
        # 如果没有检测到轮廓，尝试直接识别整张图（fallback）
        if not border_list:
            # 简单处理：将原图转为灰度并resize，尝试识别
            # 注意：这里假设原图就是单个数字
            try:
                img_gray = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)
                # 简单的二值化处理，模拟预处理效果
                _, img_thresh = cv2.threshold(img_gray, 127, 255, cv2.THRESH_BINARY_INV)
                border_list.append((img_thresh, 0, 0, 0))
            except Exception:
                pass

        for img_res, x, y, s in border_list:
            # 3. 转换为 Tensor
            try:
                img_tensor = self.transform(img_res)
                img_tensor = torch.unsqueeze(img_tensor, dim=0).to(self.device)
                
                # 4. 预测
                with torch.no_grad():
                    outputs = self.model(img_tensor)
                    probs = torch.softmax(outputs, dim=1)
                    conf, predicted = torch.max(probs, 1)
                    
                    digit = self.index_to_class[predicted.item()]
                    confidence = conf.item()
                    
                    results.append(digit)
                    confidences.append(confidence)
                    
                    # 在原图上绘制矩形框和识别结果
                    if s > 0: # 确保有有效的坐标
                        cv2.rectangle(img_display, (x, y), (x + s, y + s), (0, 255, 0), 2)
                        cv2.putText(img_display, f"{digit}", (x, y - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            except Exception as e:
                print(f"Error predicting digit: {e}")
                continue
        
        # 显示结果图片
        try:
            cv2.imshow("Prediction Result", img_display)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"无法显示图片 (可能在无头环境中运行): {e}")
        
        final_string = "".join(results)
        # 计算平均置信度
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "digit": final_string,
            "confidence": avg_confidence,
            "probabilities": confidences  # 返回每个字符的置信度列表
        }

if __name__ == '__main__':
    import sys
    import os
    
    # 添加项目根目录到 sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    from config.config_manager import ConfigManager
    
    # 1. 初始化配置和预测器
    print("初始化预测器...")
    try:
        config_manager = ConfigManager()
        predictor = Predictor(config_manager)
        predictor.load_model()
        print(f"模型加载成功: {predictor.get_model_info()}")
        
        # 2. 读取测试图片
        test_image_path = r"test2.png"
        print(f"读取测试图片: {test_image_path}")
        
        if not os.path.exists(test_image_path):
            print(f"错误: 文件不存在 - {test_image_path}")
        else:
            # 读取图片
            test_img = cv2.imread(test_image_path)
            if test_img is None:
                print("错误: 无法读取图片文件")
            else:
                # 3. 预测
                print("开始预测...")
                result = predictor.predict(test_img)
                print("-" * 30)
                print(f"预测结果: {result}")
                print("-" * 30)
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
