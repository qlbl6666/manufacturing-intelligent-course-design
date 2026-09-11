"""
YOLOv8 缺陷检测模型训练脚本
使用 NEU-DET 数据集训练目标检测模型
"""

import os
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="训练 YOLOv8 缺陷检测模型")
    parser.add_argument("--data", type=str, default="../data/processed/dataset.yaml", help="数据集配置文件")
    parser.add_argument("--model", type=str, default="yolov8s.pt", help="预训练模型")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--output", type=str, default="../models/yolov8s_neu_det.pt", help="模型保存路径")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        print("错误：请先安装 ultralytics: pip install ultralytics")
        return

    # 检查数据集配置
    if not os.path.exists(args.data):
        print(f"错误：数据集配置文件不存在: {args.data}")
        print("请先运行数据预处理脚本: python ../data/preprocess.py")
        return

    # 加载模型
    model = YOLO(args.model)
    print(f"加载预训练模型: {args.model}")

    # 训练
    print(f"开始训练: epochs={args.epochs}, batch={args.batch}, imgsz={args.imgsz}")
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        optimizer="Adam",
        lr0=0.001,
        lrf=0.01,
        patience=20,
        save=True,
        project="../runs/detect",
        name="neu_det_train",
        exist_ok=True,
        verbose=True,
    )

    # 复制最佳模型到目标路径
    best_model_path = Path("../runs/detect/neu_det_train/weights/best.pt")
    if best_model_path.exists():
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        import shutil
        shutil.copy(best_model_path, args.output)
        print(f"\n最佳模型已保存到: {args.output}")
    else:
        print(f"\n警告：未找到最佳模型，检查 runs 目录")

    # 验证
    print("\n在验证集上评估模型...")
    metrics = model.val()
    print(f"mAP@0.5: {metrics.box.map50:.4f}")
    print(f"mAP@0.5:0.95: {metrics.box.map:.4f}")


if __name__ == "__main__":
    main()
