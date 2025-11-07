import torch
import torch.nn as nn
import torch.nn.functional as F
from .base_model import BaseModel


class CNNModel(BaseModel):
    def __init__(self, input_size=(1, 28, 28), num_classes=10):
        super(CNNModel, self).__init__(input_size, num_classes)

        # 第一卷积模块：输入通道=1（灰度图），输出通道=10，卷积核=5×5
        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 10, kernel_size=5),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2)
        )

        # 第二卷积模块：输入通道=10，输出通道=20，卷积核=5×5
        self.conv2 = nn.Sequential(
            nn.Conv2d(10, 20, kernel_size=5),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2)
        )

        # 全连接模块：展平后进入两层全连接
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(320, 50),
            nn.ReLU(),
            nn.Linear(50, num_classes)
        )

        # 初始化权重
        self._initialize_weights()

    def _initialize_weights(self):
        """初始化权重"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.fc(x)
        return x
# class CNNModel(BaseModel):
#
#     def __init__(self, input_size=(1, 28, 28), num_classes=10):
#         super(CNNModel, self).__init__(input_size, num_classes)
#
#         # 第一个卷积块
#         self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
#         self.bn1 = nn.BatchNorm2d(32)
#         self.conv2 = nn.Conv2d(32, 32, kernel_size=3, padding=1)
#         self.bn2 = nn.BatchNorm2d(32)
#         self.pool1 = nn.MaxPool2d(2)
#         self.dropout1 = nn.Dropout(0.25)
#
#         # 第二个卷积块
#         self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
#         self.bn3 = nn.BatchNorm2d(64)
#         self.conv4 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
#         self.bn4 = nn.BatchNorm2d(64)
#         self.pool2 = nn.MaxPool2d(2)
#         self.dropout2 = nn.Dropout(0.25)
#
#         # 第三个卷积块
#         self.conv5 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
#         self.bn5 = nn.BatchNorm2d(128)
#         self.conv6 = nn.Conv2d(128, 128, kernel_size=3, padding=1)
#         self.bn6 = nn.BatchNorm2d(128)
#         self.pool3 = nn.MaxPool2d(2)
#         self.dropout3 = nn.Dropout(0.25)
#
#         # 全连接层
#         self.fc1 = nn.Linear(128 * 3 * 3, 256)
#         self.bn_fc = nn.BatchNorm1d(256)
#         self.dropout4 = nn.Dropout(0.5)
#         self.fc2 = nn.Linear(256, num_classes)
#
#         # 初始化权重
#         self._initialize_weights()
#
#     def _initialize_weights(self):
#         """初始化权重"""
#         for m in self.modules():
#             if isinstance(m, nn.Conv2d):
#                 nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
#                 if m.bias is not None:
#                     nn.init.constant_(m.bias, 0)
#             elif isinstance(m, nn.BatchNorm2d):
#                 nn.init.constant_(m.weight, 1)
#                 nn.init.constant_(m.bias, 0)
#             elif isinstance(m, nn.Linear):
#                 nn.init.normal_(m.weight, 0, 0.01)
#                 nn.init.constant_(m.bias, 0)
#
#     def forward(self, x):
#         # 第一个卷积块
#         x = F.relu(self.bn1(self.conv1(x)))
#         x = F.relu(self.bn2(self.conv2(x)))
#         x = self.pool1(x)
#         x = self.dropout1(x)
#
#         # 第二个卷积块
#         x = F.relu(self.bn3(self.conv3(x)))
#         x = F.relu(self.bn4(self.conv4(x)))
#         x = self.pool2(x)
#         x = self.dropout2(x)
#
#         # 第三个卷积块
#         x = F.relu(self.bn5(self.conv5(x)))
#         x = F.relu(self.bn6(self.conv6(x)))
#         x = self.pool3(x)
#         x = self.dropout3(x)
#
#         # 全连接层
#         x = x.view(x.size(0), -1)  # 展平
#         x = F.relu(self.bn_fc(self.fc1(x)))
#         x = self.dropout4(x)
#         x = self.fc2(x)
#
#         return x
