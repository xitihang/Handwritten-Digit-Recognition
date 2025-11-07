import importlib
import torch
import torch.nn as nn
from typing import Dict, Any, Tuple, Optional
from config.config_manager import ConfigManager
from utils.data_loader import create_simple_dataloader
from models.base_model import BaseModel


class ModelFactory:
    """
    input:ConfigManager
    调用create_training_components:返回包括模型、训练与验证的dataloader、优化器、损失函数
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.system_config = config_manager.get_system_config()
        self.train_config = config_manager.get_train_config()

    def create_training_components(self) -> Dict[str, Any]:
        """
        创建训练所需的所有组件
        返回包含模型、数据加载器、优化器、损失函数的字典
        """
        training_config = self.train_config
        components = {}

        # 创建模型
        components['model'] = self.create_model(training_config['model_architecture'])

        # 创建数据加载器
        components['data_loaders'] = self.create_data_loaders(
            training_config['dataset_name'],
            training_config['hyperparameters']
        )

        # 创建优化器
        components['optimizer'] = self.create_optimizer(
            components['model'],
            training_config['hyperparameters']
        )

        # 创建损失函数
        components['criterion'] = self.create_criterion(training_config['hyperparameters'])

        # 保存配置信息
        components['training_config'] = training_config

        return components

    def create_model(self, model_architecture: str) -> BaseModel:
        """
        根据模型架构名称创建模型实例
        """
        available_models = self.config_manager.get_available_models()

        if model_architecture not in available_models:
            raise ValueError(
                f"Model architecture '{model_architecture}' not found in available models: {list(available_models.keys())}")

        model_config = available_models[model_architecture]

        # 动态导入模型模块
        try:
            module_name = f"models.{model_config['model_file'].replace('.py', '')}"
            model_module = importlib.import_module(module_name)
            model_class = getattr(model_module, model_config['class_name'])
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Failed to import model class {model_config['class_name']} from {module_name}: {str(e)}")

        # 创建模型实例
        model = model_class(
            input_size=model_config['input_size'],
            num_classes=model_config['num_classes']
        )

        return model

    def create_data_loaders(self, dataset_name: str, hyperparameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建训练和验证数据加载器
        """
        available_datasets = self.config_manager.get_available_datasets()

        if dataset_name not in available_datasets:
            raise ValueError(
                f"Dataset '{dataset_name}' not found in available datasets: {list(available_datasets.keys())}")

        dataset_config = available_datasets[dataset_name]


        # 加载数据集
        train_loader, val_loader = create_simple_dataloader(
            dataset_config['path'],
            batch_size=hyperparameters['batch_size']
        )

        return {
            'train': train_loader,
            'val': val_loader
        }

    def create_optimizer(self, model: BaseModel, hyperparameters: Dict[str, Any]) -> torch.optim.Optimizer:
        """
        创建优化器
        """
        optimizer_name = hyperparameters.get('optimizer', 'adam').lower()
        learning_rate = hyperparameters.get('learning_rate', 0.001)

        if optimizer_name == 'adam':
            optimizer = torch.optim.Adam(
                model.parameters(),
                lr=learning_rate
            )
        elif optimizer_name == 'sgd':
            optimizer = torch.optim.SGD(
                model.parameters(),
                lr=learning_rate,
                momentum=0.9
            )
        elif optimizer_name == 'rmsprop':
            optimizer = torch.optim.RMSprop(
                model.parameters(),
                lr=learning_rate
            )
        else:
            raise ValueError(f"Unsupported optimizer: {optimizer_name}")

        return optimizer

    def create_criterion(self, hyperparameters: Dict[str, Any]) -> nn.Module:
        """
        创建损失函数
        """
        loss_function = hyperparameters.get('loss_function', 'cross_entropy').lower()

        if loss_function == 'cross_entropy':
            criterion = nn.CrossEntropyLoss()
        elif loss_function == 'mse':
            criterion = nn.MSELoss()
        elif loss_function == 'nll_loss':
            criterion = nn.NLLLoss()
        else:
            raise ValueError(f"Unsupported loss function: {loss_function}")

        return criterion

    def create_prediction_model(self, model_name: Optional[str] = None) -> BaseModel:
        """
        创建用于预测的模型（默认使用手机端预测模型）
        """
        if model_name is None:
            model_name = self.config_manager.get_mobile_prediction_model()

        model = self.create_model(model_name)

        # 加载预训练权重
        available_models = self.config_manager.get_available_models()
        model_config = available_models[model_name]

        if 'model_path' in model_config:
            try:
                model.load_state_dict(torch.load(model_config['model_path'], map_location='cpu'))
                model.eval()  # 设置为评估模式
            except Exception as e:
                print(f"Warning: Failed to load pre-trained weights from {model_config['model_path']}: {str(e)}")

        return model

    def get_model_input_size(self, model_architecture: str) -> list:
        """
        获取指定模型的输入尺寸
        """
        available_models = self.config_manager.get_available_models()

        if model_architecture not in available_models:
            raise ValueError(f"Model architecture '{model_architecture}' not found")

        return available_models[model_architecture]['input_size']

    def get_available_model_names(self) -> list:
        """
        获取所有可用的模型名称
        """
        return list(self.config_manager.get_available_models().keys())

    def get_available_dataset_names(self) -> list:
        """
        获取所有可用的数据集名称
        """
        return list(self.config_manager.get_available_datasets().keys())


if __name__ == '__main__':
    conf = ConfigManager()
    m = ModelFactory(conf)
    m.create_training_components()
