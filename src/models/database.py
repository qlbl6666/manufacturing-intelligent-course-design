"""
数据库初始化
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db():
    """初始化数据库表"""
    from models.user import User
    from models.detection_record import DetectionRecord
    from models.defect_detail import DefectDetail

    db.create_all()

    # 创建默认管理员账户
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("[初始化] 已创建默认管理员: admin / admin123")
