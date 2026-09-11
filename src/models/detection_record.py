"""
检测记录模型
"""

import json
from datetime import datetime
from models.database import db


class DetectionRecord(db.Model):
    """检测记录表"""

    __tablename__ = "detection_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    result_image_path = db.Column(db.String(500), nullable=True)
    defect_count = db.Column(db.Integer, default=0)
    defect_types = db.Column(db.String(500), default="[]")  # JSON 数组
    confidence_avg = db.Column(db.Float, default=0.0)
    model_version = db.Column(db.String(50), default="v1.0")
    detection_mode = db.Column(db.String(20), default="precise")  # fast / precise
    has_defect = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关联
    defect_details = db.relationship(
        "DefectDetail", backref="record", lazy=True, cascade="all, delete-orphan"
    )

    def set_defect_types(self, types_list):
        """设置缺陷类型列表"""
        self.defect_types = json.dumps(types_list, ensure_ascii=False)

    def get_defect_types(self):
        """获取缺陷类型列表"""
        try:
            return json.loads(self.defect_types)
        except (json.JSONDecodeError, TypeError):
            return []

    def to_dict(self, include_details=False):
        """序列化为字典"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "defect_count": self.defect_count,
            "defect_types": self.get_defect_types(),
            "confidence_avg": round(self.confidence_avg, 4),
            "model_version": self.model_version,
            "detection_mode": self.detection_mode,
            "has_defect": self.has_defect,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "image_url": f"/uploads/original/{self.filename}",
            "result_image_url": f"/uploads/result/{self.filename}" if self.result_image_path else None,
        }
        if include_details:
            data["details"] = [d.to_dict() for d in self.defect_details]
        return data
