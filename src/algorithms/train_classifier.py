"""
ResNet50 缺陷分类模型训练脚本
使用 NEU-DET 数据集进行迁移学习
"""

import os
import sys
import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from PIL import Image
import xml.etree.ElementTree as ET


# 类别映射
CLASS_MAPPING = {
    "crazing": 0, "inclusion": 1, "patches": 2,
    "pitted_surface": 3, "rolled-in_scale": 4, "scratches": 5,
}
CLASS_NAMES = list(CLASS_MAPPING.keys())


class NEUDETClassificationDataset(Dataset):
    """NEU-DET 分类数据集"""

    def __init__(self, image_dir, annotation_dir, transform=None):
        self.image_dir = Path(image_dir)
        self.annotation_dir = Path(annotation_dir)
        self.transform = transform
        self.samples = []

        for img_file in sorted(self.image_dir.glob("*.jpg")):
            class_name = None
            for name in CLASS_NAMES:
                if img_file.stem.startswith(name):
                    class_name = name
                    break
            if class_name:
                self.samples.append((str(img_file), CLASS_MAPPING[class_name]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, label


def get_transforms():
    """数据预处理和增强"""
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return train_transform, val_transform


def build_model(num_classes, device):
    """构建 ResNet50 迁移学习模型"""
    model = models.resnet50(pretrained=True)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)
    model = model.to(device)
    return model


def train_one_epoch(model, dataloader, criterion, optimizer, device):
    """训练一个 epoch"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in dataloader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    return running_loss / total, correct / total


def evaluate(model, dataloader, criterion, device):
    """评估模型"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in dataloader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

    return running_loss / total, correct / total


def main():
    parser = argparse.ArgumentParser(description="训练 ResNet50 缺陷分类模型")
    parser.add_argument("--data-dir", type=str, default="../data/NEU-DET", help="数据集目录")
    parser.add_argument("--output", type=str, default="../models/resnet50_neu_det.pth", help="模型保存路径")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    # 数据加载
    image_dir = os.path.join(args.data_dir, "IMAGES")
    annotation_dir = os.path.join(args.data_dir, "ANNOTATIONS")
    train_transform, val_transform = get_transforms()

    full_dataset = NEUDETClassificationDataset(image_dir, annotation_dir, train_transform)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )
    # 验证集使用验证 transform
    val_dataset.dataset.transform = val_transform

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)

    print(f"训练集: {len(train_dataset)}, 验证集: {len(val_dataset)}")

    # 构建模型
    model = build_model(len(CLASS_NAMES), device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)

    # 训练循环
    best_acc = 0.0
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    for epoch in range(args.epochs):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        print(f"Epoch {epoch+1}/{args.epochs} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), args.output)
            print(f"  -> 保存最佳模型 (Val Acc: {best_acc:.4f})")

    print(f"\n训练完成！最佳验证准确率: {best_acc:.4f}")
    print(f"模型已保存到: {args.output}")


if __name__ == "__main__":
    main()
