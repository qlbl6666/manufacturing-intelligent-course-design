"""
认证工具函数
"""

import functools
from flask import session, jsonify
from models.user import User


def login_required(f):
    """登录验证装饰器"""

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "未登录，请先登录"}), 401
        user = User.query.get(user_id)
        if not user:
            session.clear()
            return jsonify({"error": "用户不存在，请重新登录"}), 401
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """管理员验证装饰器"""

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "未登录，请先登录"}), 401
        user = User.query.get(user_id)
        if not user:
            session.clear()
            return jsonify({"error": "用户不存在，请重新登录"}), 401
        if user.role != "admin":
            return jsonify({"error": "需要管理员权限"}), 403
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    """获取当前登录用户"""
    user_id = session.get("user_id")
    if user_id:
        return User.query.get(user_id)
    return None
