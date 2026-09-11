"""
缺陷分类模型
基于 ResNet50 的迁移学习，支持 6 类工业表面缺陷分类
当模型权重不存在时，使用基于图像纹理特征的模拟推理
"""

import os
import numpy as np
import cv2

from config import Config


class DefectClassifier:
    """缺陷分类器"""

    def __init__(self, model_path=None, device="cpu"):
        self.classes = Config.DEFECT_CLASSES
        self.num_classes = len(self.classes)
        self.device = device
        self.model = None
        self.model_loaded = False

        if model_path and os.path.exists(model_path):
            self._load_model(model_path)
        else:
            print("[分类器] 未找到模型权重，使用模拟推理模式")

    def _load_model(self, model_path):
        """加载 PyTorch 模型"""
        try:
            import torch
            import torch.nn as nn
            from torchvision import models

            # 构建 ResNet50 模型
            self.model = models.resnet50(pretrained=False)
            num_ftrs = self.model.fc.in_features
            self.model.fc = nn.Linear(num_ftrs, self.num_classes)

            # 加载权重
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            print(f"[分类器] 模型加载成功: {model_path}")
        except Exception as e:
            print(f"[分类器] 模型加载失败: {e}，使用模拟推理模式")
            self.model = None
            self.model_loaded = False

    def predict(self, image_tensor):
        """
        预测缺陷类别
        参数: image_tensor - 形状 (1, 3, 224, 224) 的 numpy 数组
        返回: (预测类别索引, 各类别概率数组)
        """
        if self.model_loaded:
            return self._predict_real(image_tensor)
        else:
            return self._predict_simulated(image_tensor)

    def _predict_real(self, image_tensor):
        """真实模型推理"""
        import torch
        with torch.no_grad():
            input_tensor = torch.from_numpy(image_tensor).to(self.device)
            outputs = self.model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1).cpu().numpy()[0]
            pred_class = int(np.argmax(probabilities))
        return pred_class, probabilities

    def _predict_simulated(self, image_tensor):
        """
        模拟推理：基于图像纹理特征估算缺陷类型
        使用边缘密度、局部方差、亮度分布等特征启发式判断
        """
        # 从张量还原图像 (CHW -> HWC, [0,1] -> [0,255])
        img = (np.transpose(image_tensor[0], (1, 2, 0)) * 255).astype(np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # 特征提取
        # 1. 边缘密度（Canny）
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size

        # 2. 局部方差（纹理粗糙度）
        kernel_size = 15
        mean = cv2.blur(gray.astype(np.float32), (kernel_size, kernel_size))
        sq_mean = cv2.blur((gray.astype(np.float32)) ** 2, (kernel_size, kernel_size))
        local_var = np.mean(sq_mean - mean ** 2)

        # 3. 亮度统计
        brightness = np.mean(gray)
        brightness_std = np.std(gray)

        # 4. 暗斑比例（低亮度像素占比）
        dark_ratio = np.sum(gray < 80) / gray.size

        # 5. 亮斑比例（高亮度像素占比）
        bright_ratio = np.sum(gray > 200) / gray.size

        # 基于特征的启发式分类（模拟模型输出概率）
        scores = np.zeros(self.num_classes, dtype=np.float32)

        # 裂纹(crazing): 高边缘密度，网状结构
        scores[0] = 0.15 + edge_density * 2.0 + (brightness_std / 100) * 0.2

        # 夹杂(inclusion): 暗斑，局部高方差
        scores[1] = 0.15 + dark_ratio * 1.5 + local_var / 5000

        # 斑块(patches): 大面积明暗不均
        scores[2] = 0.15 + brightness_std / 80 + dark_ratio * 0.5

        # 麻点(pitted_surface): 多暗点，高边缘密度
        scores[3] = 0.15 + dark_ratio * 2.0 + edge_density * 0.5

        # 氧化皮(rolled-in_scale): 亮斑，粗糙纹理
        scores[4] = 0.15 + bright_ratio * 1.5 + local_var / 4000

        # 划痕(scratches): 线性边缘，方向性
        scores[5] = 0.15 + edge_density * 1.5 + brightness_std / 100

        # 添加随机扰动（模拟模型不确定性）
        np.random.seed(int(np.sum(gray) % 10000))
        scores += np.random.uniform(-0.05, 0.05, self.num_classes)
        scores = np.maximum(scores, 0.01)

        # Softmax 归一化
        exp_scores = np.exp(scores - np.max(scores))
        probabilities = exp_scores / np.sum(exp_scores)

        pred_class = int(np.argmax(probabilities))
        return pred_class, probabilities

    def get_class_name(self, class_idx):
        """获取类别名称"""
        if 0 <= class_idx < self.num_classes:
            return self.classes[class_idx]
        return "unknown"

    def get_class_name_cn(self, class_idx):
        """获取类别中文名称"""
        class_name = self.get_class_name(class_idx)
        return Config.DEFECT_CLASSES_CN.get(class_name, "未知")


# 全局单例
_classifier_instance = None


def get_classifier():
    """获取分类器单例"""
    global _classifier_instance
    if _classifier_instance is None:
        model_path = os.path.join(Config.MODEL_DIR, Config.CLASSIFIER_MODEL)
        _classifier_instance = DefectClassifier(model_path, Config.DEVICE)
    return _classifier_instance
