import os
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import random
from pathlib import Path
import torchvision.transforms as transforms


class SimpleImageDataset(Dataset):
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]

        # 读取图片
        image = Image.open(img_path).convert('L')

        # 应用变换（包括resize）
        if self.transform:
            image = self.transform(image)

        return image, label


def create_simple_dataloader(data_dir, batch_size, img_size=(28, 28), validation_split=0.2):
    """
    简单创建数据加载器
    Args:
        data_dir: 图片文件夹路径
        batch_size: 批次大小
        img_size: 统一resize的尺寸
        validation_split: 验证集比例
    Returns:
        train_loader, val_loader
    """

    # 1. 收集所有图片文件
    dataset_dir = Path(__file__).parent.parent
    # dataset_dir = os.path.join(dataset_dir, "storage/datasets")
    data_dir = os.path.join(dataset_dir, data_dir)
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_paths = []
    data_dir = Path(data_dir)

    for ext in image_extensions:
        image_paths.extend(data_dir.glob(f'*{ext}'))

    if len(image_paths) == 0:
        raise ValueError(f"在 {data_dir} 中没有找到图片文件")

    print(f"找到 {len(image_paths)} 张图片")

    # 2. 提取标签（文件名最后一个字符转换为数字）
    labels = []
    valid_image_paths = []

    for img_path in image_paths:
        try:
            # 获取文件名（不含扩展名）的最后一个字符
            label_char = img_path.stem[-1]
            # 转换为数字
            label = int(label_char)
            labels.append(label)
            valid_image_paths.append(img_path)
        except (ValueError, IndexError):
            print(f"跳过文件 {img_path.name}，无法从文件名提取数字标签")

    print(f"成功处理 {len(valid_image_paths)} 张图片")

    # 3. 定义数据变换（统一resize）
    transform = transforms.Compose([
        transforms.Resize(img_size),
        transforms.ToTensor()
    ])

    # 4. 随机划分训练集和验证集 (8:2)
    combined = list(zip(valid_image_paths, labels))
    random.shuffle(combined)
    split_idx = int(len(combined) * (1 - validation_split))

    train_data = combined[:split_idx]
    val_data = combined[split_idx:]

    train_paths, train_labels = zip(*train_data) if train_data else ([], [])
    val_paths, val_labels = zip(*val_data) if val_data else ([], [])

    print(f"训练集: {len(train_paths)} 张图片")
    print(f"验证集: {len(val_paths)} 张图片")

    # 5. 创建数据集和数据加载器
    train_dataset = SimpleImageDataset(train_paths, train_labels, transform=transform)
    val_dataset = SimpleImageDataset(val_paths, val_labels, transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader


# 使用示例
if __name__ == "__main__":
    # 简单调用
    train_loader, val_loader = create_simple_dataloader(
        data_dir="./data/images",
        batch_size=16,
        img_size=(128, 128)
    )

    # 测试一下
    for images, labels in train_loader:
        print(f"图片尺寸: {images.shape}")  # [batch_size, 3, 128, 128]
        print(f"标签: {labels}")  # 数字标签
        break