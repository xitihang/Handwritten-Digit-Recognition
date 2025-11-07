import torch
import torch.nn as nn
import torch.nn.functional as F
from .base_model import BaseModel


class MLPModel(BaseModel):

    def __init__(self, input_size=784, num_classes=10, hidden_sizes=[512, 256, 128]):
        super(MLPModel, self).__init__(input_size, num_classes)

        # 构建隐藏层
        layers = []
        prev_size = input_size

        for i, hidden_size in enumerate(hidden_sizes):
            layers.append(nn.Linear(prev_size, hidden_size))
            layers.append(nn.BatchNorm1d(hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.3 if i < len(hidden_sizes) - 1 else 0.5))
            prev_size = hidden_size

        self.hidden_layers = nn.Sequential(*layers)

        # 输出层
        self.output_layer = nn.Linear(prev_size, num_classes)

        # 初始化权重
        self._initialize_weights()

    def _initialize_weights(self):
        """初始化权重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        # 如果输入是图像格式 (batch, 1, 28, 28)，先展平
        if x.dim() == 4:
            x = x.view(x.size(0), -1)

        x = self.hidden_layers(x)
        x = self.output_layer(x)
        return x

