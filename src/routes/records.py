"""
检测记录管理 API
列表查询、详情查看、删除、导出
"""

import csv
import io
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, make_response
from models.database import db
from models.detection_record import DetectionRecord
from utils.auth import login_required, get_current_user
from config import Config

records_bp = Blueprint("records", __name__)


@records_bp.route("", methods=["GET"])
@login_required
def list_records():
    """
    获取当前用户的检测记录列表
    支持分页、筛选、排序
    参数: page, per_page, defect_type, has_defect, start_date, end_date
    """
    user = get_current_user()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    defect_type = request.args.get("defect_type", "").strip()
    has_defect = request.args.get("has_defect", type=str)
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    query = DetectionRecord.query.filter_by(user_id=user.id)

    # 筛选
    if has_defect is not None and has_defect != "":
        query = query.filter_by(has_defect=(has_defect.lower() == "true"))

    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(DetectionRecord.created_at >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(DetectionRecord.created_at < end)
        except ValueError:
            pass

    # 排序（按时间倒序）
    query = query.order_by(DetectionRecord.created_at.desc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    records = pagination.items

    # 按缺陷类型筛选（需要在内存中过滤，因为 defect_types 是 JSON 字符串）
    if defect_type:
        filtered = []
        for r in records:
            if defect_type in r.get_defect_types():
                filtered.append(r)
        records = filtered

    return jsonify({
        "records": [r.to_dict() for r in records],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    })


@records_bp.route("/<int:record_id>", methods=["GET"])
@login_required
def get_record(record_id):
    """获取单条检测记录详情"""
    user = get_current_user()
    record = DetectionRecord.query.filter_by(id=record_id, user_id=user.id).first()

    if not record:
        return jsonify({"error": "记录不存在"}), 404

    return jsonify({"record": record.to_dict(include_details=True)})


@records_bp.route("/<int:record_id>", methods=["DELETE"])
@login_required
def delete_record(record_id):
    """删除检测记录"""
    user = get_current_user()
    record = DetectionRecord.query.filter_by(id=record_id, user_id=user.id).first()

    if not record:
        return jsonify({"error": "记录不存在"}), 404

    # 删除关联的图片文件
    try:
        import os
        if record.image_path and os.path.exists(record.image_path):
            os.remove(record.image_path)
        if record.result_image_path and os.path.exists(record.result_image_path):
            os.remove(record.result_image_path)
    except Exception:
        pass

    db.session.delete(record)
    db.session.commit()

    return jsonify({"message": "记录已删除"})


@records_bp.route("/<int:record_id>/export", methods=["GET"])
@login_required
def export_record(record_id):
    """导出单条检测记录为 CSV"""
    user = get_current_user()
    record = DetectionRecord.query.filter_by(id=record_id, user_id=user.id).first()

    if not record:
        return jsonify({"error": "记录不存在"}), 404

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["字段", "值"])
    writer.writerow(["记录ID", record.id])
    writer.writerow(["文件名", record.filename])
    writer.writerow(["检测时间", record.created_at.strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["检测模式", record.detection_mode])
    writer.writerow(["是否有缺陷", "是" if record.has_defect else "否"])
    writer.writerow(["缺陷数量", record.defect_count])
    writer.writerow(["缺陷类型", ", ".join(record.get_defect_types())])
    writer.writerow(["平均置信度", f"{record.confidence_avg:.4f}"])
    writer.writerow([])
    writer.writerow(["缺陷详情"])
    writer.writerow(["序号", "类型", "中文名称", "置信度", "X", "Y", "宽", "高", "面积"])
    for i, d in enumerate(record.defect_details, 1):
        writer.writerow([
            i, d.defect_type, d.defect_type_cn, f"{d.confidence:.4f}",
            d.bbox_x, d.bbox_y, d.bbox_w, d.bbox_h, d.area,
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=record_{record_id}.csv"
    return response


@records_bp.route("/export/all", methods=["GET"])
@login_required
def export_all_records():
    """导出所有检测记录为 CSV"""
    user = get_current_user()
    records = DetectionRecord.query.filter_by(user_id=user.id).order_by(
        DetectionRecord.created_at.desc()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "记录ID", "文件名", "检测时间", "检测模式", "是否有缺陷",
        "缺陷数量", "缺陷类型", "平均置信度",
    ])
    for r in records:
        writer.writerow([
            r.id, r.filename, r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            r.detection_mode, "是" if r.has_defect else "否",
            r.defect_count, ", ".join(r.get_defect_types()),
            f"{r.confidence_avg:.4f}",
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=all_records.csv"
    return response
