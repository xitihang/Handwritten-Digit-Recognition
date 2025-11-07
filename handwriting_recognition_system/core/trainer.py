# handwriting_recognition_system/core/trainer.py
import json
import os
import time
import torch
from typing import Dict, Any, Callable


class Trainer:
    """
    负责模型训练逻辑：
    1. 接收ConfigManager -> 使用ModelFactory创建训练组件
    2. 执行训练与验证循环
    3. 实时输出训练日志，并支持外部回调函数推送训练进度
    4. 保存训练完成的模型到 storage/trained_models/
    """

    def __init__(self, components, progress_callback: Callable[[Dict[str, Any]], None] = None):
        self.components = components
        self.progress_callback = progress_callback  # 用于web_server实时推送训练状态
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logs = []  # 用于记录所有epoch的日志

    def train(self):
        # === 初始化组件 ===
        model = self.components["model"].to(self.device)
        data_loaders = self.components["data_loaders"]
        optimizer = self.components["optimizer"]
        criterion = self.components["criterion"]
        training_config = self.components["training_config"]

        train_loader = data_loaders["train"]
        val_loader = data_loaders["val"]

        num_epochs = training_config["hyperparameters"].get("epochs", 10)
        model_name = training_config["save_model_name"]
        # 确保存储目录存在
        save_dir = os.path.join(os.path.dirname(__file__), '../storage/trained_models')
        os.makedirs(save_dir, exist_ok=True)

        print(f"开始训练模型: {model_name}")
        print(f"保存路径: {os.path.abspath(save_dir)}")

        # === 训练循环 ===
        for epoch in range(num_epochs):
            model.train()
            running_loss, correct, total = 0.0, 0, 0

            for images, labels in train_loader:
                images, labels = images.to(self.device), labels.to(self.device)

                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                running_loss += loss.item() * images.size(0)
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()

            train_loss = running_loss / total
            train_acc = correct / total

            # === 验证 ===
            model.eval()
            val_loss, val_correct, val_total = 0.0, 0, 0
            with torch.no_grad():
                for images, labels in val_loader:
                    images, labels = images.to(self.device), labels.to(self.device)
                    outputs = model(images)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item() * images.size(0)
                    _, predicted = outputs.max(1)
                    val_total += labels.size(0)
                    val_correct += predicted.eq(labels).sum().item()

            val_loss /= val_total
            val_acc = val_correct / val_total

            log = {
                "epoch": epoch + 1,
                "train_loss": round(train_loss, 4),
                "train_acc": round(train_acc, 4),
                "val_loss": round(val_loss, 4),
                "val_acc": round(val_acc, 4)
            }
            # === 保存日志到内存 ===
            self.logs.append(log)
            # === 实时打印与推送 ===
            print(f"[Epoch {epoch+1}/{num_epochs}] "
                  f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}, "
                  f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}, ")

            if self.progress_callback:
                self.progress_callback(log)

        # === 保存模型 ===
        save_path = os.path.join(save_dir, f"{model_name}.pth")
        torch.save(model.state_dict(), save_path)
        print(f"✅ 训练完成，模型已保存到: {os.path.abspath(save_path)}")

        # === 保存训练日志 ===
        log_path = os.path.join(save_dir, f"{model_name}_log.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=4, ensure_ascii=False)
        print(f"📘 训练日志已保存到: {os.path.abspath(log_path)}")


        return {
            "model_path": save_path,
            "final_train_acc": train_acc,
            "final_val_acc": val_acc
        }
