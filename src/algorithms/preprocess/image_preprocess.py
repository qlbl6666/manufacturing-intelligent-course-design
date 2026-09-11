"""
图像预处理模块
功能：尺寸归一化、像素归一化、图像增强、格式转换
"""

import cv2
import numpy as np


def load_image(image_path):
    """
    加载图像，统一为 BGR 三通道
    返回: (BGR图像, 原始宽, 原始高)
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        # 尝试用 PIL 兜底
        try:
            from PIL import Image
            pil_img = Image.open(image_path).convert("RGB")
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except Exception:
            raise ValueError(f"无法读取图像: {image_path}")

    h, w = img.shape[:2]
    return img, w, h


def letterbox(img, target_size=640, color=(114, 114, 114)):
    """
    Letterbox 缩放：保持宽高比，填充到目标尺寸
    返回: (缩放后图像, 缩放比例, (左边距, 上边距))
    """
    h, w = img.shape[:2]
    scale = min(target_size / w, target_size / h)
    new_w, new_h = int(w * scale), int(h * scale)

    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    canvas = np.full((target_size, target_size, 3), color, dtype=np.uint8)
    top = (target_size - new_h) // 2
    left = (target_size - new_w) // 2
    canvas[top:top + new_h, left:left + new_w] = resized

    return canvas, scale, (left, top)


def normalize_image(img):
    """
    像素归一化: [0,255] -> [0,1]，BGR->RGB，HWC->CHW
    返回: 形状 (1, 3, H, W) 的 numpy 数组
    """
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_norm = img_rgb.astype(np.float32) / 255.0
    # HWC -> CHW
    img_chw = np.transpose(img_norm, (2, 0, 1))
    # 增加 batch 维度
    img_batch = np.expand_dims(img_chw, axis=0)
    return img_batch


def preprocess_for_classifier(image_path, target_size=224):
    """
    分类模型预处理流水线
    返回: (预处理后张量, 原始图像, 原始尺寸)
    """
    img, orig_w, orig_h = load_image(image_path)
    # ResNet 输入 224x224
    resized = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_LINEAR)
    tensor = normalize_image(resized)
    return tensor, img, (orig_w, orig_h)


def preprocess_for_detector(image_path, target_size=640):
    """
    检测模型预处理流水线
    返回: (预处理后张量, letterbox图像, 缩放比例, 填充偏移, 原始图像, 原始尺寸)
    """
    img, orig_w, orig_h = load_image(image_path)
    lb_img, scale, (left, top) = letterbox(img, target_size)
    tensor = normalize_image(lb_img)
    return tensor, lb_img, scale, (left, top), img, (orig_w, orig_h)


def enhance_contrast(img):
    """对比度增强（CLAHE）"""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge((l, a, b))
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def denoise(img):
    """高斯去噪"""
    return cv2.GaussianBlur(img, (3, 3), 0)
