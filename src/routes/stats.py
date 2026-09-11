"""
统计仪表盘 API
检测量趋势、缺陷类型分布、模型性能指标
"""

from datetime import datetime, timedelta
from collections import Counter
from flask import Blueprint, jsonify
from models.detection_record import DetectionRecord
from models.defect_detail import DefectDetail
from utils.auth import login_required, get_current_user
from config import Config

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/overview", methods=["GET"])
@login_required
def overview():
    """获取统计概览数据"""
    user = get_current_user()

    total_records = DetectionRecord.query.filter_by(user_id=user.id).count()
    defect_records = DetectionRecord.query.filter_by(user_id=user.id, has_defect=True).count()
    total_defects = DefectDetail.query.join(DetectionRecord).filter(
        DetectionRecord.user_id == user.id
    ).count()

    # 最近 7 天检测量
    today = datetime.utcnow().date()
    daily_counts = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        start = datetime.combine(date, datetime.min.time())
        end = start + timedelta(days=1)
        count = DetectionRecord.query.filter(
            DetectionRecord.user_id == user.id,
            DetectionRecord.created_at >= start,
            DetectionRecord.created_at < end,
        ).count()
        daily_counts.append({"date": date.strftime("%Y-%m-%d"), "count": count})

    # 缺陷类型分布
    defect_type_counter = Counter()
    records = DetectionRecord.query.filter_by(user_id=user.id, has_defect=True).all()
    for r in records:
        for dt in r.get_defect_types():
            defect_type_counter[dt] += 1

    defect_distribution = []
    for cls in Config.DEFECT_CLASSES:
        count = defect_type_counter.get(cls, 0)
        defect_distribution.append({
            "type": cls,
            "type_cn": Config.DEFECT_CLASSES_CN.get(cls, cls),
            "count": count,
        })

    # 平均置信度
    avg_confidence = 0.0
    if total_defects > 0:
        from sqlalchemy import func
        from models.database import db
        result = db.session.query(func.avg(DefectDetail.confidence)).join(
            DetectionRecord
        ).filter(DetectionRecord.user_id == user.id).scalar()
        avg_confidence = float(result) if result else 0.0

    # 缺陷率
    defect_rate = (defect_records / total_records * 100) if total_records > 0 else 0

    return jsonify({
        "overview": {
            "total_records": total_records,
            "defect_records": defect_records,
            "total_defects": total_defects,
            "defect_rate": round(defect_rate, 2),
            "avg_confidence": round(avg_confidence, 4),
        },
        "daily_trend": daily_counts,
        "defect_distribution": defect_distribution,
    })


@stats_bp.route("/model-performance", methods=["GET"])
@login_required
def model_performance():
    """获取模型性能指标（基于历史检测数据统计）"""
    user = get_current_user()

    # 按检测模式统计
    fast_count = DetectionRecord.query.filter_by(
        user_id=user.id, detection_mode="fast"
    ).count()
    precise_count = DetectionRecord.query.filter_by(
        user_id=user.id, detection_mode="precise"
    ).count()

    # 各类别的平均置信度
    class_confidence = {}
    for cls in Config.DEFECT_CLASSES:
        details = DefectDetail.query.join(DetectionRecord).filter(
            DetectionRecord.user_id == user.id,
            DefectDetail.defect_type == cls,
        ).all()
        if details:
            avg_conf = sum(d.confidence for d in details) / len(details)
            class_confidence[cls] = {
                "type_cn": Config.DEFECT_CLASSES_CN.get(cls, cls),
                "count": len(details),
                "avg_confidence": round(avg_conf, 4),
            }

    return jsonify({
        "model_version": "v1.0",
        "detection_mode_usage": {
            "fast": fast_count,
            "precise": precise_count,
        },
        "class_performance": class_confidence,
    })
