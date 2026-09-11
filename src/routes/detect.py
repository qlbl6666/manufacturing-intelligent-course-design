"""
缺陷检测 API
图片上传、执行检测、返回结果
"""

import os
from flask import Blueprint, request, jsonify, current_app
from models.database import db
from models.detection_record import DetectionRecord
from models.defect_detail import DefectDetail
from utils.auth import login_required, get_current_user
from utils.file_handler import save_upload_file, allowed_file
from algorithms.inference.pipeline import get_pipeline
from algorithms.postprocess.visualize import save_result_image
from config import Config

detect_bp = Blueprint("detect", __name__)


@detect_bp.route("/upload", methods=["POST"])
@login_required
def upload_and_detect():
    """
    上传图片并执行缺陷检测
    支持 multipart/form-data 上传，字段名: image
    可选参数: mode (fast/precise), conf_threshold
    """
    user = get_current_user()

    # 检查文件
    if "image" not in request.files:
        return jsonify({"error": "未找到上传文件，字段名应为 image"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "未选择文件"}), 400

    # 检查文件类型
    if not allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
        return jsonify({
            "error": f"不支持的文件格式，仅支持: {', '.join(Config.ALLOWED_EXTENSIONS)}"
        }), 400

    # 获取参数
    mode = request.form.get("mode", Config.DEFAULT_DETECTION_MODE)
    if mode not in ("fast", "precise"):
        mode = Config.DEFAULT_DETECTION_MODE

    conf_threshold = request.form.get("conf_threshold", type=float)
    if conf_threshold is not None:
        conf_threshold = max(0.0, min(1.0, conf_threshold))

    # 保存上传文件
    save_path, unique_name, original_name = save_upload_file(
        file, current_app.config["UPLOAD_FOLDER"], Config.ALLOWED_EXTENSIONS
    )
    if save_path is None:
        return jsonify({"error": "文件保存失败"}), 500

    try:
        # 执行检测
        pipeline = get_pipeline()
        result = pipeline.run(save_path, mode=mode, conf_threshold=conf_threshold)

        if "error" in result:
            return jsonify({"error": f"检测失败: {result['error']}"}), 500

        # 保存结果图像
        result_image_path = None
        if result.get("result_image") is not None:
            result_filename = unique_name
            result_image_path = os.path.join(current_app.config["RESULT_FOLDER"], result_filename)
            save_result_image(result["result_image"], result_image_path)

        # 保存检测记录到数据库
        record = DetectionRecord(
            user_id=user.id,
            filename=unique_name,
            image_path=save_path,
            result_image_path=result_image_path,
            defect_count=result["defect_count"],
            confidence_avg=result["confidence_avg"],
            model_version="v1.0",
            detection_mode=mode,
            has_defect=result["has_defect"],
        )
        record.set_defect_types(result["defect_types"])
        db.session.add(record)
        db.session.flush()  # 获取 record.id

        # 保存缺陷详情
        for det in result.get("detections", []):
            detail = DefectDetail(
                record_id=record.id,
                defect_type=det["class_name"],
                defect_type_cn=det["class_name_cn"],
                confidence=det["confidence"],
                bbox_x=det["bbox"][0],
                bbox_y=det["bbox"][1],
                bbox_w=det["bbox"][2],
                bbox_h=det["bbox"][3],
                area=det["area"],
            )
            db.session.add(detail)

        db.session.commit()

        # 构建响应
        response = {
            "message": "检测完成",
            "record_id": record.id,
            "original_filename": original_name,
            "has_defect": result["has_defect"],
            "predicted_class": result["predicted_class"],
            "predicted_class_cn": result["predicted_class_cn"],
            "class_probabilities": result["class_probabilities"],
            "defect_count": result["defect_count"],
            "defect_types": result["defect_types"],
            "confidence_avg": round(result["confidence_avg"], 4),
            "mode": mode,
            "inference_time": result["inference_time"],
            "detections": result.get("detections", []),
            "image_url": f"/uploads/original/{unique_name}",
            "result_image_url": f"/uploads/result/{unique_name}" if result_image_path else None,
        }

        return jsonify(response)

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"检测过程出错: {str(e)}"}), 500


@detect_bp.route("/batch", methods=["POST"])
@login_required
def batch_detect():
    """批量上传检测（最多10张）"""
    user = get_current_user()

    if "images" not in request.files:
        return jsonify({"error": "未找到上传文件，字段名应为 images"}), 400

    files = request.files.getlist("images")
    if len(files) == 0:
        return jsonify({"error": "未选择文件"}), 400
    if len(files) > 10:
        return jsonify({"error": "批量上传最多 10 张图片"}), 400

    mode = request.form.get("mode", Config.DEFAULT_DETECTION_MODE)
    results = []

    for file in files:
        if not allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
            results.append({"filename": file.filename, "error": "不支持的文件格式"})
            continue

        save_path, unique_name, original_name = save_upload_file(
            file, current_app.config["UPLOAD_FOLDER"], Config.ALLOWED_EXTENSIONS
        )
        if save_path is None:
            results.append({"filename": file.filename, "error": "文件保存失败"})
            continue

        try:
            pipeline = get_pipeline()
            result = pipeline.run(save_path, mode=mode)

            # 保存结果图像
            result_image_path = None
            if result.get("result_image") is not None:
                result_image_path = os.path.join(current_app.config["RESULT_FOLDER"], unique_name)
                save_result_image(result["result_image"], result_image_path)

            # 保存记录
            record = DetectionRecord(
                user_id=user.id,
                filename=unique_name,
                image_path=save_path,
                result_image_path=result_image_path,
                defect_count=result["defect_count"],
                confidence_avg=result["confidence_avg"],
                model_version="v1.0",
                detection_mode=mode,
                has_defect=result["has_defect"],
            )
            record.set_defect_types(result["defect_types"])
            db.session.add(record)
            db.session.flush()

            for det in result.get("detections", []):
                detail = DefectDetail(
                    record_id=record.id,
                    defect_type=det["class_name"],
                    defect_type_cn=det["class_name_cn"],
                    confidence=det["confidence"],
                    bbox_x=det["bbox"][0],
                    bbox_y=det["bbox"][1],
                    bbox_w=det["bbox"][2],
                    bbox_h=det["bbox"][3],
                    area=det["area"],
                )
                db.session.add(detail)

            results.append({
                "filename": original_name,
                "has_defect": result["has_defect"],
                "predicted_class_cn": result["predicted_class_cn"],
                "defect_count": result["defect_count"],
                "confidence_avg": round(result["confidence_avg"], 4),
                "result_image_url": f"/uploads/result/{unique_name}" if result_image_path else None,
            })

        except Exception as e:
            results.append({"filename": original_name, "error": str(e)})

    db.session.commit()
    return jsonify({"message": "批量检测完成", "results": results, "total": len(results)})
