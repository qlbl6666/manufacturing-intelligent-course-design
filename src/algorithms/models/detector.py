"""
缺陷检测模型
基于 YOLOv8 的目标检测，支持 6 类工业表面缺陷定位
当模型权重不存在时，使用基于图像特征的模拟推理
"""

import os
import numpy as np
import cv2

from config import Config


class DefectDetector:
    """缺陷检测器"""

    def __init__(self, model_path=None, device="cpu", conf_threshold=0.25, iou_threshold=0.45):
        self.classes = Config.DEFECT_CLASSES
        self.num_classes = len(self.classes)
        self.device = device
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.model = None
        self.model_loaded = False

        if model_path and os.path.exists(model_path):
            self._load_model(model_path)
        else:
            print("[检测器] 未找到模型权重，使用模拟推理模式")

    def _load_model(self, model_path):
        """加载 YOLOv8 模型"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            self.model_loaded = True
            print(f"[检测器] 模型加载成功: {model_path}")
        except Exception as e:
            print(f"[检测器] 模型加载失败: {e}，使用模拟推理模式")
            self.model = None
            self.model_loaded = False

    def detect(self, image_tensor, orig_size, scale=1.0, offset=(0, 0)):
        """
        执行缺陷检测
        参数:
            image_tensor: (1, 3, 640, 640) numpy 数组
            orig_size: (原始宽, 原始高)
            scale: letterbox 缩放比例
            offset: (左边距, 上边距)
        返回:
            detections: 列表，每个元素为 dict:
                {class_id, class_name, class_name_cn, confidence, bbox:[x,y,w,h], area}
        """
        if self.model_loaded:
            return self._detect_real(image_tensor, orig_size, scale, offset)
        else:
            return self._detect_simulated(image_tensor, orig_size)

    def _detect_real(self, image_tensor, orig_size, scale, offset):
        """真实 YOLOv8 推理"""
        import torch
        results = self.model(image_tensor, verbose=False)[0]
        detections = []
        orig_w, orig_h = orig_size

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            if conf < self.conf_threshold:
                continue

            # YOLO 输出是 letterbox 坐标，需要映射回原图
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            # 减去填充，除以缩放比例
            x1 = max(0, (x1 - offset[0]) / scale)
            y1 = max(0, (y1 - offset[1]) / scale)
            x2 = min(orig_w, (x2 - offset[0]) / scale)
            y2 = min(orig_h, (y2 - offset[1]) / scale)

            w = int(x2 - x1)
            h = int(y2 - y1)
            area = w * h

            class_name = self.classes[cls_id] if cls_id < self.num_classes else "unknown"
            detections.append({
                "class_id": cls_id,
                "class_name": class_name,
                "class_name_cn": Config.DEFECT_CLASSES_CN.get(class_name, "未知"),
                "confidence": conf,
                "bbox": [int(x1), int(y1), w, h],
                "area": area,
            })

        return detections

    def _detect_simulated(self, image_tensor, orig_size):
        """
        模拟检测：基于图像纹理特征在图像中定位疑似缺陷区域
        使用滑动窗口 + 局部异常评分
        """
        # 还原图像
        img = (np.transpose(image_tensor[0], (1, 2, 0)) * 255).astype(np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        orig_w, orig_h = orig_size
        # 输入是 640x640，需要映射回原图尺寸
        scale_x = orig_w / 640.0
        scale_y = orig_h / 640.0

        # 使用局部方差找到异常区域
        kernel_size = 31
        mean = cv2.blur(gray.astype(np.float32), (kernel_size, kernel_size))
        sq_mean = cv2.blur((gray.astype(np.float32)) ** 2, (kernel_size, kernel_size))
        local_var = sq_mean - mean ** 2

        # 边缘密度
        edges = cv2.Canny(gray, 50, 150)
        edge_density_map = cv2.blur(edges.astype(np.float32), (kernel_size, kernel_size))

        # 异常分数 = 局部方差 + 边缘密度
        anomaly_map = local_var / (local_var.max() + 1e-6) + edge_density_map / (edge_density_map.max() + 1e-6)

        # 阈值化找到高异常区域
        threshold = np.mean(anomaly_map) + np.std(anomaly_map) * 0.8
        anomaly_mask = (anomaly_map > threshold).astype(np.uint8) * 255

        # 形态学操作合并邻近区域
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        anomaly_mask = cv2.morphologyEx(anomaly_mask, cv2.MORPH_CLOSE, kernel)
        anomaly_mask = cv2.morphologyEx(anomaly_mask, cv2.MORPH_OPEN, kernel)

        # 查找轮廓
        contours, _ = cv2.findContours(anomaly_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        np.random.seed(int(np.sum(gray) % 10000))

        for contour in contours:
            area = cv2.contourArea(contour)
            # 过滤太小的区域
            if area < 200:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            # 过滤太大的区域（超过图像 60%）
            if w * h > 0.6 * 640 * 640:
                continue

            # 基于区域内的特征判断缺陷类型
            roi = gray[y:y + h, x:x + w]
            roi_edges = cv2.Canny(roi, 50, 150)
            roi_edge_density = np.sum(roi_edges > 0) / roi_edges.size if roi.size > 0 else 0
            roi_dark = np.sum(roi < 80) / roi.size if roi.size > 0 else 0
            roi_bright = np.sum(roi > 200) / roi.size if roi.size > 0 else 0
            roi_std = np.std(roi) if roi.size > 0 else 0

            # 启发式分类
            type_scores = {
                0: roi_edge_density * 3,           # 裂纹
                1: roi_dark * 2,                   # 夹杂
                2: roi_std / 50,                   # 斑块
                3: roi_dark * 3 + roi_edge_density, # 麻点
                4: roi_bright * 2,                 # 氧化皮
                5: roi_edge_density * 2,           # 划痕
            }
            cls_id = max(type_scores, key=type_scores.get)
            confidence = 0.3 + np.random.uniform(0, 0.5) + min(type_scores[cls_id], 0.3)
            confidence = min(confidence, 0.98)

            if confidence < self.conf_threshold:
                continue

            # 映射回原图坐标
            orig_x = int(x * scale_x)
            orig_y = int(y * scale_y)
            orig_w_box = int(w * scale_x)
            orig_h_box = int(h * scale_y)
            orig_area = orig_w_box * orig_h_box

            class_name = self.classes[cls_id]
            detections.append({
                "class_id": cls_id,
                "class_name": class_name,
                "class_name_cn": Config.DEFECT_CLASSES_CN.get(class_name, "未知"),
                "confidence": float(confidence),
                "bbox": [orig_x, orig_y, orig_w_box, orig_h_box],
                "area": orig_area,
            })

        # 按置信度排序，最多返回 10 个
        detections.sort(key=lambda x: x["confidence"], reverse=True)
        return detections[:10]


# 全局单例
_detector_instance = None


def get_detector():
    """获取检测器单例"""
    global _detector_instance
    if _detector_instance is None:
        model_path = os.path.join(Config.MODEL_DIR, Config.DETECTOR_MODEL)
        _detector_instance = DefectDetector(
            model_path, Config.DEVICE,
            Config.DEFAULT_CONF_THRESHOLD,
            Config.DEFAULT_IOU_THRESHOLD,
        )
    return _detector_instance
