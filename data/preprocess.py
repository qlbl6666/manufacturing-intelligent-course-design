"""
NEU-DET 数据集预处理脚本
功能：
1. 解析 PASCAL VOC XML 标注
2. 转换为 YOLO TXT 格式（归一化坐标）
3. 按比例划分训练集/验证集/测试集（分层抽样）
4. 图像尺寸归一化（可选）
5. 生成 YOLOv8 训练配置文件 dataset.yaml
"""

import os
import sys
import json
import shutil
import random
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

import cv2
import numpy as np


# 类别映射
CLASS_MAPPING = {
    "crazing": 0,
    "inclusion": 1,
    "patches": 2,
    "pitted_surface": 3,
    "rolled-in_scale": 4,
    "scratches": 5,
}

CLASS_NAMES = list(CLASS_MAPPING.keys())


def parse_xml(xml_path):
    """解析 PASCAL VOC XML 文件，返回标注框列表"""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    boxes = []
    for obj in root.findall("object"):
        name = obj.find("name").text.strip()
        if name not in CLASS_MAPPING:
            print(f"警告：未知类别 {name}，跳过")
            continue
        class_id = CLASS_MAPPING[name]
        bndbox = obj.find("bndbox")
        xmin = float(bndbox.find("xmin").text)
        ymin = float(bndbox.find("ymin").text)
        xmax = float(bndbox.find("xmax").text)
        ymax = float(bndbox.find("ymax").text)
        boxes.append((class_id, xmin, ymin, xmax, ymax))

    # 获取图像尺寸
    size = root.find("size")
    width = int(size.find("width").text)
    height = int(size.find("height").text)

    return boxes, width, height


def convert_to_yolo(boxes, img_width, img_height):
    """将 VOC 格式转换为 YOLO 格式（归一化中心坐标+宽高）"""
    yolo_lines = []
    for class_id, xmin, ymin, xmax, ymax in boxes:
        # 中心坐标
        x_center = (xmin + xmax) / 2.0 / img_width
        y_center = (ymin + ymax) / 2.0 / img_height
        # 宽高
        w = (xmax - xmin) / img_width
        h = (ymax - ymin) / img_height
        # 裁剪到 [0, 1]
        x_center = max(0.0, min(1.0, x_center))
        y_center = max(0.0, min(1.0, y_center))
        w = max(0.0, min(1.0, w))
        h = max(0.0, min(1.0, h))
        yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")
    return yolo_lines


def get_image_class_from_filename(filename):
    """从文件名推断类别（NEU-DET 命名规则：类别_编号.jpg）"""
    name = Path(filename).stem
    for class_name in CLASS_NAMES:
        if name.startswith(class_name):
            return class_name
    return None


def split_dataset(image_files, train_ratio, val_ratio, test_ratio, seed=42):
    """分层抽样划分数据集"""
    random.seed(seed)

    # 按类别分组
    class_groups = defaultdict(list)
    for img_file in image_files:
        class_name = get_image_class_from_filename(img_file)
        if class_name:
            class_groups[class_name].append(img_file)
        else:
            class_groups["_unknown"].append(img_file)

    train_files, val_files, test_files = [], [], []

    for class_name, files in class_groups.items():
        random.shuffle(files)
        n = len(files)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        train_files.extend(files[:n_train])
        val_files.extend(files[n_train:n_train + n_val])
        test_files.extend(files[n_train + n_val:])

    return train_files, val_files, test_files


def process_image(src_path, dst_path, target_size=None):
    """处理单张图片：读取、可选resize、保存"""
    img = cv2.imread(str(src_path), cv2.IMREAD_COLOR)
    if img is None:
        print(f"警告：无法读取图片 {src_path}")
        return False

    if target_size and (img.shape[0] != target_size or img.shape[1] != target_size):
        img = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_LINEAR)

    cv2.imwrite(str(dst_path), img)
    return True


def generate_dataset_yaml(output_dir, class_names):
    """生成 YOLOv8 训练配置文件"""
    yaml_content = f"""# NEU-DET 数据集配置
path: {output_dir.resolve()}
train: images/train
val: images/val
test: images/test

nc: {len(class_names)}
names: {class_names}
"""
    yaml_path = output_dir / "dataset.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"已生成数据集配置：{yaml_path}")


def generate_index(output_dir, train_files, val_files, test_files, annotations_dir):
    """生成数据集索引 CSV"""
    index_path = output_dir / "dataset_index.csv"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("filename,class,split,num_boxes\n")
        for split_name, files in [("train", train_files), ("val", val_files), ("test", test_files)]:
            for img_file in files:
                class_name = get_image_class_from_filename(img_file)
                xml_path = annotations_dir / (Path(img_file).stem + ".xml")
                num_boxes = 0
                if xml_path.exists():
                    try:
                        boxes, _, _ = parse_xml(xml_path)
                        num_boxes = len(boxes)
                    except Exception:
                        pass
                f.write(f"{img_file},{class_name},{split_name},{num_boxes}\n")
    print(f"已生成数据索引：{index_path}")


def main():
    parser = argparse.ArgumentParser(description="NEU-DET 数据集预处理")
    parser.add_argument("--source", type=str, default="./NEU-DET", help="原始数据集目录")
    parser.add_argument("--output", type=str, default="./processed", help="预处理输出目录")
    parser.add_argument("--ratio", type=str, default="7:2:1", help="训练:验证:测试 比例")
    parser.add_argument("--img-size", type=int, default=640, help="目标图像尺寸（0表示不resize）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    args = parser.parse_args()

    source_dir = Path(args.source)
    output_dir = Path(args.output)
    images_dir = source_dir / "IMAGES"
    annotations_dir = source_dir / "ANNOTATIONS"

    # 检查输入目录
    if not images_dir.exists():
        print(f"错误：图片目录不存在 {images_dir}")
        print("请先下载 NEU-DET 数据集并解压到 data/NEU-DET/ 目录")
        sys.exit(1)

    # 解析比例
    ratios = [float(x) for x in args.ratio.split(":")]
    train_ratio, val_ratio, test_ratio = [r / sum(ratios) for r in ratios]

    # 创建输出目录
    for split in ["train", "val", "test"]:
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    # 获取所有图片
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    image_files = [f.name for f in images_dir.iterdir() if f.suffix.lower() in image_extensions]
    print(f"找到 {len(image_files)} 张图片")

    # 划分数据集
    train_files, val_files, test_files = split_dataset(image_files, train_ratio, val_ratio, test_ratio, args.seed)
    print(f"训练集: {len(train_files)}, 验证集: {len(val_files)}, 测试集: {len(test_files)}")

    # 处理每个划分
    target_size = args.img_size if args.img_size > 0 else None
    stats = {"success": 0, "failed": 0, "no_annotation": 0}

    for split_name, files in [("train", train_files), ("val", val_files), ("test", test_files)]:
        print(f"\n处理 {split_name} 集...")
        for i, img_file in enumerate(files):
            if (i + 1) % 100 == 0:
                print(f"  进度: {i+1}/{len(files)}")

            src_img_path = images_dir / img_file
            dst_img_path = output_dir / "images" / split_name / img_file
            dst_label_path = output_dir / "labels" / split_name / (Path(img_file).stem + ".txt")

            # 处理图片
            if not process_image(src_img_path, dst_img_path, target_size):
                stats["failed"] += 1
                continue

            # 处理标注
            xml_path = annotations_dir / (Path(img_file).stem + ".xml")
            if xml_path.exists():
                try:
                    boxes, img_w, img_h = parse_xml(xml_path)
                    # 如果 resize 了，需要重新计算尺寸
                    if target_size:
                        yolo_lines = convert_to_yolo(boxes, target_size, target_size)
                    else:
                        yolo_lines = convert_to_yolo(boxes, img_w, img_h)
                    with open(dst_label_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(yolo_lines) + "\n")
                    stats["success"] += 1
                except Exception as e:
                    print(f"  警告：标注解析失败 {xml_path}: {e}")
                    # 写空标注文件
                    with open(dst_label_path, "w", encoding="utf-8") as f:
                        f.write("")
                    stats["success"] += 1
            else:
                # 无标注文件（可能是无缺陷样本）
                with open(dst_label_path, "w", encoding="utf-8") as f:
                    f.write("")
                stats["no_annotation"] += 1
                stats["success"] += 1

    # 生成配置文件和索引
    generate_dataset_yaml(output_dir, CLASS_NAMES)
    generate_index(output_dir, train_files, val_files, test_files, annotations_dir)

    # 保存类别映射
    with open(output_dir / "class_mapping.json", "w", encoding="utf-8") as f:
        json.dump(CLASS_MAPPING, f, ensure_ascii=False, indent=2)

    print(f"\n预处理完成！")
    print(f"  成功: {stats['success']}")
    print(f"  失败: {stats['failed']}")
    print(f"  无标注: {stats['no_annotation']}")
    print(f"  输出目录: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
