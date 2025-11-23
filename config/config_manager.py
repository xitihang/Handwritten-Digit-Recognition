import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.prediction_config_path = os.path.join(self.config_dir, "prediction_config.json")
        self.train_config_path = os.path.join(self.config_dir, "train_config.json")
        self.system_config_path = os.path.join(self.config_dir, "system_config.json")

        # 确保配置文件存在
        self._ensure_config_files_exist()

    def _ensure_config_files_exist(self):
        """确保配置文件存在，如果不存在则创建默认配置"""
        os.makedirs(self.config_dir, exist_ok=True)

        # 预测配置
        if not os.path.exists(self.prediction_config_path):
            print(f"缺少配置文件-prediction_config")

        # 训练配置模板
        if not os.path.exists(self.train_config_path):
            print(f"缺少配置文件-train_config")

        # 系统配置
        if not os.path.exists(self.system_config_path):
            print(f"缺少配置文件-system_config")

    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Failed to load config file {file_path}: {str(e)}")

    def _save_json(self, file_path: str, data: Dict[str, Any]):
        """保存JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Failed to save config file {file_path}: {str(e)}")

    def create_training_config(self, training_request: Dict[str, Any]) -> Dict[str, Any]:
        """根据训练请求生成训练配置对象"""
        # 获取系统配置中的默认值
        system_config = self.get_system_config()
        training_defaults = system_config.get("training_defaults", {})

        # 创建训练配置
        training_config = {
            "training_id": f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "model_architecture": training_request.get("model_architecture", ""),
            "dataset_name": training_request.get("dataset_name", ""),
            "save_model_name": training_request.get("save_model_name", ""),
            "hyperparameters": {
                "batch_size": training_request.get("batch_size", training_defaults.get("batch_size", 64)),
                "learning_rate": training_request.get("learning_rate", training_defaults.get("learning_rate", 0.001)),
                "epochs": training_request.get("epochs", training_defaults.get("epochs", 50)),
                "optimizer": training_request.get("optimizer", training_defaults.get("optimizer", "adam")),
                "loss_function": training_request.get("loss_function",
                                                      training_defaults.get("loss_function", "cross_entropy"))

            },
        }

        return training_config

    def get_train_config(self) -> Dict[str, Any]:
        """获取训练配置"""
        return self._load_json(self.train_config_path)

    def get_mobile_prediction_model(self) -> str:
        """获取手机端预测使用的模型名称"""
        config = self._load_json(self.prediction_config_path)
        return config.get("mobile_prediction_model", "mlp_model")

    def set_mobile_prediction_model(self, model_name: str):
        """设置手机端预测使用的模型"""
        config = self._load_json(self.prediction_config_path)
        config["mobile_prediction_model"] = model_name
        config["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_json(self.prediction_config_path, config)

    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self._load_json(self.system_config_path)

    def get_available_models(self) -> Dict[str, Any]:
        """获取可用的模型列表"""
        system_config = self.get_system_config()
        return system_config.get("available_models", {})

    def get_available_datasets(self) -> Dict[str, Any]:
        """获取可用的数据集列表"""
        system_config = self.get_system_config()
        return system_config.get("available_datasets", {})

    def add_new_model(self, model_id: str, model_config: Dict[str, Any]):
        """添加新模型到系统配置"""
        system_config = self.get_system_config()
        system_config["available_models"][model_id] = model_config
        self._save_json(self.system_config_path, system_config)

    def add_new_dataset(self, dataset_id: str, dataset_config: Dict[str, Any]):
        """添加新数据集到系统配置"""
        system_config = self.get_system_config()
        system_config["available_datasets"][dataset_id] = dataset_config
        self._save_json(self.system_config_path, system_config)

    def get_prediction_weights_path(self) -> Optional[str]:
        """获取预测使用的权重文件路径"""
        config = self._load_json(self.prediction_config_path)
        return config.get("model_weights_path")

    def set_prediction_weights_path(self, weights_path: str):
        """设置预测使用的权重文件路径"""
        config = self._load_json(self.prediction_config_path)
        config["model_weights_path"] = weights_path
        config["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_json(self.prediction_config_path, config)
