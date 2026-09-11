"""
用户模型
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db


class User(db.Model):
    """用户表"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")  # user / admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    detection_records = db.relationship(
        "DetectionRecord", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """设置密码（哈希存储）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """校验密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """序列化为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
