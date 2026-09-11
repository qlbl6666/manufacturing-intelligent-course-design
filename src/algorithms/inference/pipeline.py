"""
检测推理流水线
整合分类模型和检测模型，提供统一的检测接口
"""

import time
import os
import numpy as np

from config import Config
from algorithms.preprocess.image_preprocess import (
    preprocess_for_classifier,
    preprocess_for_detector,
)
from algorithms.models.classifier import get_classifier
from algorithms.models.detector import get_detector
from algorithms.postprocess.visualize import draw_detections


class DetectionPipeline:
    """检测流水线"""

    def __init__(self):
        self.classifier = get_classifier()
        self.detector = get_detector()

    def run(self, image_path, mode="precise", conf_threshold=None):
        """
        执行完整检测流水线

        参数:
            image_path: 图像文件路径
            mode: "fast"（仅分类）/ "precise"（分类+检测定位）
            conf_threshold: 置信度阈值，None 则使用默认值

        返回:
            result dict: {
                "has_defect": bool,
                "predicted_class": str,
                "predicted_class_cn": str,
                "class_probabilities": dict,
                "detections": list,
                "defect_count": int,
                "defect_types": list,
                "confidence_avg": float,
                "mode": str,
                "inference_time": float,
                "result_image": numpy array (BGR),
            }
        """
        start_time = time.time()

        if conf_threshold is not None:
            self.detector.conf_threshold = conf_threshold

        result = {
            "has_defect": False,
            "predicted_class": None,
            "predicted_class_cn": None,
            "class_probabilities": {},
            "detections": [],
            "defect_count": 0,
            "defect_types": [],
            "confidence_avg": 0.0,
            "mode": mode,
            "inference_time": 0.0,
            "result_image": None,
        }

        try:
            # === 第一步：分类 ===
            cls_tensor, orig_img, (orig_w, orig_h) = preprocess_for_classifier(image_path, target_size=224)
            pred_class, probabilities = self.classifier.predict(cls_tensor)

            result["predicted_class"] = self.classifier.get_class_name(pred_class)
            result["predicted_class_cn"] = self.classifier.get_class_name_cn(pred_class)
            result["class_probabilities"] = {
                self.classifier.classes[i]: round(float(probabilities[i]), 4)
                for i in range(len(self.classifier.classes))
            }

            # 判断是否有缺陷（最大概率 > 0.5 视为有缺陷）
            max_prob = float(np.max(probabilities)) if hasattr(probabilities, '__iter__') else 0.0
            result["has_defect"] = max_prob > 0.5

            # === 第二步：检测定位（精确模式） ===
            if mode == "precise" and result["has_defect"]:
                det_tensor, lb_img, scale, offset, orig_img_full, _ = preprocess_for_detector(image_path, target_size=640)
                detections = self.detector.detect(
                    det_tensor, (orig_w, orig_h), scale, offset
                )
                result["detections"] = detections
                result["defect_count"] = len(detections)
                result["defect_types"] = list(set(d["class_name"] for d in detections))
                if detections:
                    result["confidence_avg"] = sum(d["confidence"] for d in detections) / len(detections)

                # 绘制检测结果
                result["result_image"] = draw_detections(orig_img_full, detections)
            else:
                # 快速模式或无缺陷，直接使用原图
                result["result_image"] = orig_img
                if result["has_defect"]:
                    result["defect_count"] = 1
                    result["defect_types"] = [result["predicted_class"]]
                    result["confidence_avg"] = max_prob

        except Exception as e:
            print(f"[检测流水线] 推理出错: {e}")
            import traceback
            traceback.print_exc()
            result["error"] = str(e)

        result["inference_time"] = round(time.time() - start_time, 3)
        return result


# 全局单例
_pipeline_instance = None


def get_pipeline():
    """获取检测流水线单例"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DetectionPipeline()
    return _pipeline_instance
