"""
用户认证 API
注册、登录、登出、获取当前用户信息
"""

from flask import Blueprint, request, jsonify, session
from models.database import db
from models.user import User
from utils.auth import login_required, get_current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """用户注册"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求数据为空"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    # 参数校验
    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400
    if len(username) < 3 or len(username) > 50:
        return jsonify({"error": "用户名长度需在 3-50 个字符之间"}), 400
    if len(password) < 6:
        return jsonify({"error": "密码长度不能少于 6 位"}), 400
    if password != confirm_password:
        return jsonify({"error": "两次输入的密码不一致"}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "用户名已存在"}), 409

    # 创建用户
    user = User(username=username, role="user")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "注册成功",
        "user": user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求数据为空"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "用户名或密码错误"}), 401

    # 保存登录状态
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    return jsonify({
        "message": "登录成功",
        "user": user.to_dict(),
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """用户登出"""
    session.clear()
    return jsonify({"message": "已退出登录"})


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_me():
    """获取当前用户信息"""
    user = get_current_user()
    return jsonify({"user": user.to_dict()})
