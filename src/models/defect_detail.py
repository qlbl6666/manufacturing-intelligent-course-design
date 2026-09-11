"""
缺陷详情模型
"""

from models.database import db


class DefectDetail(db.Model):
    """缺陷详情表"""

    __tablename__ = "defect_details"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    record_id = db.Column(db.Integer, db.ForeignKey("detection_records.id"), nullable=False, index=True)
    defect_type = db.Column(db.String(50), nullable=False)
    defect_type_cn = db.Column(db.String(50), nullable=True)
    confidence = db.Column(db.Float, nullable=False)
    bbox_x = db.Column(db.Integer, default=0)
    bbox_y = db.Column(db.Integer, default=0)
    bbox_w = db.Column(db.Integer, default=0)
    bbox_h = db.Column(db.Integer, default=0)
    area = db.Column(db.Integer, default=0)  # 像素面积

    def to_dict(self):
        """序列化为字典"""
        return {
            "id": self.id,
            "defect_type": self.defect_type,
            "defect_type_cn": self.defect_type_cn,
            "confidence": round(self.confidence, 4),
            "bbox": {
                "x": self.bbox_x,
                "y": self.bbox_y,
                "w": self.bbox_w,
                "h": self.bbox_h,
            },
            "area": self.area,
        }
