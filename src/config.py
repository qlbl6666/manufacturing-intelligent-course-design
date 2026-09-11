"""
应用配置
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent


class Config:
    """基础配置"""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "defect-detection-secret-key-2024")
    DEBUG = True

    # 数据库
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'defect_detection.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文件上传
    UPLOAD_FOLDER = str(PROJECT_ROOT / "uploads" / "original")
    RESULT_FOLDER = str(PROJECT_ROOT / "uploads" / "result")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp"}

    # 模型配置
    MODEL_DIR = str(PROJECT_ROOT / "models")
    CLASSIFIER_MODEL = "resnet50_neu_det.pth"
    DETECTOR_MODEL = "yolov8s_neu_det.pt"
    DEFAULT_CONF_THRESHOLD = 0.25
    DEFAULT_IOU_THRESHOLD = 0.45
    DEFAULT_DETECTION_MODE = "precise"  # fast / precise

    # 类别定义
    DEFECT_CLASSES = [
        "crazing",        # 裂纹
        "inclusion",      # 夹杂
        "patches",        # 斑块
        "pitted_surface", # 麻点
        "rolled-in_scale",# 氧化皮
        "scratches",      # 划痕
    ]
    DEFECT_CLASSES_CN = {
        "crazing": "裂纹",
        "inclusion": "夹杂",
        "patches": "斑块",
        "pitted_surface": "麻点",
        "rolled-in_scale": "氧化皮",
        "scratches": "划痕",
    }
    # 每个类别的标注颜色 (BGR)
    DEFECT_COLORS = {
        "crazing": (0, 0, 255),        # 红
        "inclusion": (0, 255, 0),      # 绿
        "patches": (255, 0, 0),        # 蓝
        "pitted_surface": (0, 255, 255),   # 黄
        "rolled-in_scale": (255, 0, 255),  # 紫
        "scratches": (255, 255, 0),    # 青
    }

    # 推理设备
    DEVICE = "cpu"  # 有GPU可改为 "cuda"
