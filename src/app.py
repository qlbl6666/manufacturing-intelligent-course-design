"""
制造智能技术课程设计 - 基于深度学习的工业产品表面缺陷智能检测系统
Flask 应用入口
"""

import os
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS

from config import Config
from models.database import db, init_db
from routes.auth import auth_bp
from routes.detect import detect_bp
from routes.records import records_bp
from routes.stats import stats_bp
from routes.model_manage import model_bp


def create_app():
    """创建并配置 Flask 应用"""
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    app.config.from_object(Config)

    # 初始化扩展
    CORS(app)
    db.init_app(app)

    # 创建上传目录
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["RESULT_FOLDER"], exist_ok=True)

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(detect_bp, url_prefix="/api/detect")
    app.register_blueprint(records_bp, url_prefix="/api/records")
    app.register_blueprint(stats_bp, url_prefix="/api/stats")
    app.register_blueprint(model_bp, url_prefix="/api/models")

    # 页面路由
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/records")
    def records_page():
        return render_template("records.html")

    @app.route("/stats")
    def stats_page():
        return render_template("stats.html")

    @app.route("/models")
    def models_page():
        return render_template("models.html")

    # 健康检查
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "缺陷检测系统"})

    # 上传文件静态访问
    @app.route("/uploads/<folder>/<filename>")
    def serve_upload(folder, filename):
        base = Path(app.config["UPLOAD_FOLDER"]).parent
        return send_from_directory(str(base / folder), filename)

    # 初始化数据库
    with app.app_context():
        init_db()

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("  基于深度学习的工业产品表面缺陷智能检测系统")
    print("  访问地址: http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
