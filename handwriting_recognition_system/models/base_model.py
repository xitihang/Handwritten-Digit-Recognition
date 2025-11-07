import torch
import torch.nn as nn
from abc import ABC, abstractmethod


class BaseModel(nn.Module, ABC):
    """基础模型类"""

    def __init__(self, input_size, num_classes=10):
        super(BaseModel, self).__init__()
        self.input_size = input_size
        self.num_classes = num_classes

    @abstractmethod
    def forward(self, x):
        pass

    def get_optimizer(self, learning_rate=0.001):
        """获取优化器"""
        return torch.optim.Adam(self.parameters(), lr=learning_rate)

    def get_loss_fn(self):
        """获取损失函数"""
        return nn.CrossEntropyLoss()