"""
模型管理 API（管理员功能）
模型版本切换、阈值配置、模型列表
"""

from flask import Blueprint, request, jsonify
from utils.auth import admin_required
from config import Config
from algorithms.models.classifier import get_classifier
from algorithms.models.detector import get_detector

model_bp = Blueprint("models", __name__)

# 内存中的模型配置
_model_config = {
    "active_classifier": "resnet50_v1",
    "active_detector": "yolov8s_v1",
    "conf_threshold": Config.DEFAULT_CONF_THRESHOLD,
    "iou_threshold": Config.DEFAULT_IOU_THRESHOLD,
}


@model_bp.route("", methods=["GET"])
@admin_required
def list_models():
    """获取可用模型列表"""
    classifier = get_classifier()
    detector = get_detector()

    models = [
        {
            "name": "ResNet50 分类模型",
            "type": "classifier",
            "version": "v1.0",
            "status": "loaded" if classifier.model_loaded else "simulated",
            "classes": len(classifier.classes),
            "input_size": "224x224",
        },
        {
            "name": "YOLOv8s 检测模型",
            "type": "detector",
            "version": "v1.0",
            "status": "loaded" if detector.model_loaded else "simulated",
            "classes": len(detector.classes),
            "input_size": "640x640",
        },
    ]

    return jsonify({
        "models": models,
        "active_config": _model_config,
    })


@model_bp.route("/threshold", methods=["PUT"])
@admin_required
def update_threshold():
    """更新检测阈值"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求数据为空"}), 400

    conf_threshold = data.get("conf_threshold")
    iou_threshold = data.get("iou_threshold")

    if conf_threshold is not None:
        conf_threshold = float(conf_threshold)
        if not (0.0 <= conf_threshold <= 1.0):
            return jsonify({"error": "置信度阈值必须在 0-1 之间"}), 400
        _model_config["conf_threshold"] = conf_threshold
        get_detector().conf_threshold = conf_threshold

    if iou_threshold is not None:
        iou_threshold = float(iou_threshold)
        if not (0.0 <= iou_threshold <= 1.0):
            return jsonify({"error": "IoU 阈值必须在 0-1 之间"}), 400
        _model_config["iou_threshold"] = iou_threshold
        get_detector().iou_threshold = iou_threshold

    return jsonify({
        "message": "阈值已更新",
        "config": _model_config,
    })


@model_bp.route("/switch", methods=["PUT"])
@admin_required
def switch_model():
    """切换模型版本"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求数据为空"}), 400

    model_type = data.get("model_type")
    version = data.get("version")

    if model_type not in ("classifier", "detector"):
        return jsonify({"error": "模型类型必须是 classifier 或 detector"}), 400

    if model_type == "classifier":
        _model_config["active_classifier"] = version
    else:
        _model_config["active_detector"] = version

    return jsonify({
        "message": f"{model_type} 模型已切换到 {version}",
        "config": _model_config,
    })
