"""
模型评估脚本
计算分类模型的准确率、精确率、召回率、F1、混淆矩阵
"""

import os
import argparse
import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision import models, transforms
from PIL import Image
from pathlib import Path

CLASS_MAPPING = {
    "crazing": 0, "inclusion": 1, "patches": 2,
    "pitted_surface": 3, "rolled-in_scale": 4, "scratches": 5,
}
CLASS_NAMES = list(CLASS_MAPPING.keys())


def load_model(model_path, num_classes, device):
    """加载训练好的模型"""
    model = models.resnet50(pretrained=False)
    num_ftrs = model.fc.in_features
    model.fc = torch.nn.Linear(num_ftrs, num_classes)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    return model


def compute_metrics(y_true, y_pred, num_classes):
    """计算评估指标"""
    # 混淆矩阵
    confusion = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        confusion[t][p] += 1

    # 每类指标
    precision_list, recall_list, f1_list = [], [], []
    for i in range(num_classes):
        tp = confusion[i][i]
        fp = sum(confusion[j][i] for j in range(num_classes) if j != i)
        fn = sum(confusion[i][j] for j in range(num_classes) if j != i)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        precision_list.append(precision)
        recall_list.append(recall)
        f1_list.append(f1)

    accuracy = sum(confusion[i][i] for i in range(num_classes)) / len(y_true) if y_true else 0

    return {
        "accuracy": accuracy,
        "precision": precision_list,
        "recall": recall_list,
        "f1": f1_list,
        "confusion_matrix": confusion,
    }


def main():
    parser = argparse.ArgumentParser(description="评估分类模型")
    parser.add_argument("--model", type=str, default="../models/resnet50_neu_det.pth")
    parser.add_argument("--data-dir", type=str, default="../data/NEU-DET/IMAGES")
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    device = torch.device(args.device)

    if not os.path.exists(args.model):
        print(f"模型文件不存在: {args.model}")
        print("请先运行 train_classifier.py 训练模型")
        return

    model = load_model(args.model, len(CLASS_NAMES), device)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # 加载测试数据
    y_true, y_pred = [], []
    image_dir = Path(args.data_dir)

    for img_file in sorted(image_dir.glob("*.jpg")):
        class_name = None
        for name in CLASS_NAMES:
            if img_file.stem.startswith(name):
                class_name = name
                break
        if not class_name:
            continue

        image = Image.open(img_file).convert("RGB")
        tensor = transform(image).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(tensor)
            pred = output.argmax(1).item()

        y_true.append(CLASS_MAPPING[class_name])
        y_pred.append(pred)

    # 计算指标
    metrics = compute_metrics(y_true, y_pred, len(CLASS_NAMES))

    print("=" * 60)
    print("模型评估结果")
    print("=" * 60)
    print(f"总体准确率: {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print()
    print(f"{'类别':<15} {'精确率':<10} {'召回率':<10} {'F1':<10}")
    print("-" * 45)
    for i, name in enumerate(CLASS_NAMES):
        print(f"{name:<15} {metrics['precision'][i]:<10.4f} {metrics['recall'][i]:<10.4f} {metrics['f1'][i]:<10.4f}")
    print()
    print("混淆矩阵:")
    print("真实\\预测", "  ".join(f"{n[:6]:>7}" for n in CLASS_NAMES))
    for i, name in enumerate(CLASS_NAMES):
        row = "  ".join(f"{metrics['confusion_matrix'][i][j]:>7}" for j in range(len(CLASS_NAMES)))
        print(f"{name[:10]:<10} {row}")


if __name__ == "__main__":
    main()
