"""
自动化测试套件
测试 API 接口、数据库模型、算法模块
运行方式: python -m pytest tests/ -v
"""

import os
import sys
import io
import json
import tempfile
import pytest
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import create_app
from models.database import db as _db
from models.user import User


@pytest.fixture
def app():
    """创建测试应用（使用内存数据库）"""
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        # 清空并重建数据库
        _db.drop_all()
        _db.create_all()
        # 创建测试用户
        user = User(username="testuser", role="user")
        user.set_password("test123")
        admin = User(username="testadmin", role="admin")
        admin.set_password("admin123")
        _db.session.add_all([user, admin])
        _db.session.commit()

    yield app


@pytest.fixture
def client(app):
    """测试客户端"""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """已登录的测试客户端（普通用户）"""
    client.post("/api/auth/login", json={"username": "testuser", "password": "test123"})
    return client


@pytest.fixture
def admin_client(client):
    """已登录的管理员客户端"""
    client.post("/api/auth/login", json={"username": "testadmin", "password": "admin123"})
    return client


# ============== 健康检查测试 ==============

class TestHealth:
    def test_health_endpoint(self, client):
        """测试健康检查接口"""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"


# ============== 认证测试 ==============

class TestAuth:
    def test_register_success(self, client):
        """测试注册成功"""
        resp = client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "pass123",
            "confirm_password": "pass123",
        })
        assert resp.status_code == 201
        assert "注册成功" in resp.get_json()["message"]

    def test_register_duplicate(self, client):
        """测试重复注册"""
        resp = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "pass123",
            "confirm_password": "pass123",
        })
        assert resp.status_code == 409

    def test_register_password_mismatch(self, client):
        """测试密码不一致"""
        resp = client.post("/api/auth/register", json={
            "username": "user2",
            "password": "pass123",
            "confirm_password": "wrong",
        })
        assert resp.status_code == 400

    def test_login_success(self, client):
        """测试登录成功"""
        resp = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "test123",
        })
        assert resp.status_code == 200
        assert resp.get_json()["user"]["username"] == "testuser"

    def test_login_wrong_password(self, client):
        """测试密码错误"""
        resp = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrong",
        })
        assert resp.status_code == 401

    def test_get_me(self, auth_client):
        """测试获取当前用户"""
        resp = auth_client.get("/api/auth/me")
        assert resp.status_code == 200
        assert resp.get_json()["user"]["username"] == "testuser"

    def test_get_me_unauthorized(self, client):
        """测试未登录获取用户信息"""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_logout(self, auth_client):
        """测试登出"""
        resp = auth_client.post("/api/auth/logout")
        assert resp.status_code == 200
        # 登出后再访问需要登录的接口
        resp2 = auth_client.get("/api/auth/me")
        assert resp2.status_code == 401


# ============== 检测接口测试 ==============

class TestDetection:
    def _create_test_image(self):
        """创建测试图片"""
        from PIL import Image
        img = Image.new("RGB", (200, 200), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        return buf

    def test_detect_no_auth(self, client):
        """测试未登录检测"""
        resp = client.post("/api/detect/upload", data={})
        assert resp.status_code == 401

    def test_detect_no_file(self, auth_client):
        """测试未上传文件"""
        resp = auth_client.post("/api/detect/upload", data={})
        assert resp.status_code == 400

    def test_detect_success(self, auth_client):
        """测试检测成功"""
        img_buf = self._create_test_image()
        resp = auth_client.post(
            "/api/detect/upload",
            data={"image": (img_buf, "test.jpg"), "mode": "fast"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "has_defect" in data
        assert "predicted_class" in data
        assert "defect_count" in data
        assert "inference_time" in data

    def test_detect_precise_mode(self, auth_client):
        """测试精确模式检测"""
        img_buf = self._create_test_image()
        resp = auth_client.post(
            "/api/detect/upload",
            data={"image": (img_buf, "test.jpg"), "mode": "precise"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["mode"] == "precise"
        assert "detections" in data


# ============== 记录管理测试 ==============

class TestRecords:
    def test_list_records(self, auth_client):
        """测试获取记录列表"""
        resp = auth_client.get("/api/records?page=1&per_page=10")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "records" in data
        assert "pagination" in data

    def test_record_detail_not_found(self, auth_client):
        """测试获取不存在的记录"""
        resp = auth_client.get("/api/records/99999")
        assert resp.status_code == 404

    def test_record_delete(self, auth_client):
        """测试删除记录（先创建再删除）"""
        from PIL import Image
        img = Image.new("RGB", (100, 100), color=(100, 100, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        # 创建一条记录
        create_resp = auth_client.post(
            "/api/detect/upload",
            data={"image": (buf, "del_test.jpg"), "mode": "fast"},
            content_type="multipart/form-data",
        )
        record_id = create_resp.get_json()["record_id"]

        # 删除
        del_resp = auth_client.delete(f"/api/records/{record_id}")
        assert del_resp.status_code == 200

        # 确认已删除
        get_resp = auth_client.get(f"/api/records/{record_id}")
        assert get_resp.status_code == 404


# ============== 统计测试 ==============

class TestStats:
    def test_overview(self, auth_client):
        """测试统计概览"""
        resp = auth_client.get("/api/stats/overview")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "overview" in data
        assert "daily_trend" in data
        assert "defect_distribution" in data

    def test_model_performance(self, auth_client):
        """测试模型性能统计"""
        resp = auth_client.get("/api/stats/model-performance")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "model_version" in data
        assert "detection_mode_usage" in data


# ============== 模型管理测试 ==============

class TestModelManage:
    def test_list_models_admin(self, admin_client):
        """测试管理员获取模型列表"""
        resp = admin_client.get("/api/models")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "models" in data
        assert "active_config" in data

    def test_list_models_non_admin(self, auth_client):
        """测试普通用户无权限"""
        resp = auth_client.get("/api/models")
        assert resp.status_code == 403

    def test_update_threshold_admin(self, admin_client):
        """测试管理员更新阈值"""
        resp = admin_client.put("/api/models/threshold", json={
            "conf_threshold": 0.35,
            "iou_threshold": 0.5,
        })
        assert resp.status_code == 200
        assert resp.get_json()["config"]["conf_threshold"] == 0.35


# ============== 算法模块测试 ==============

class TestAlgorithms:
    def test_image_preprocess(self, tmp_path):
        """测试图像预处理"""
        from PIL import Image
        from algorithms.preprocess.image_preprocess import load_image, letterbox, normalize_image

        # 创建测试图
        img_path = tmp_path / "test.jpg"
        Image.new("RGB", (300, 200), color=(128, 128, 128)).save(img_path)

        img, w, h = load_image(str(img_path))
        assert w == 300 and h == 200
        assert img.shape == (200, 300, 3)

        lb_img, scale, offset = letterbox(img, target_size=640)
        assert lb_img.shape == (640, 640, 3)
        assert scale > 0

        tensor = normalize_image(lb_img)
        assert tensor.shape == (1, 3, 640, 640)
        assert tensor.min() >= 0 and tensor.max() <= 1

    def test_classifier_simulated(self, tmp_path):
        """测试分类器模拟推理"""
        from PIL import Image
        from algorithms.models.classifier import DefectClassifier
        from algorithms.preprocess.image_preprocess import preprocess_for_classifier

        img_path = tmp_path / "test.jpg"
        Image.new("RGB", (224, 224), color=(100, 100, 100)).save(img_path)

        classifier = DefectClassifier()  # 无模型文件，使用模拟模式
        tensor, _, _ = preprocess_for_classifier(str(img_path))
        pred_class, probs = classifier.predict(tensor)

        assert 0 <= pred_class < 6
        assert len(probs) == 6
        assert abs(sum(probs) - 1.0) < 0.01

    def test_detector_simulated(self, tmp_path):
        """测试检测器模拟推理"""
        from PIL import Image
        from algorithms.models.detector import DefectDetector
        from algorithms.preprocess.image_preprocess import preprocess_for_detector

        img_path = tmp_path / "test.jpg"
        Image.new("RGB", (640, 640), color=(100, 100, 100)).save(img_path)

        detector = DefectDetector()  # 模拟模式
        tensor, _, scale, offset, orig_img, (orig_w, orig_h) = preprocess_for_detector(str(img_path))
        detections = detector.detect(tensor, (orig_w, orig_h), scale, offset)

        assert isinstance(detections, list)
        for det in detections:
            assert "class_id" in det
            assert "class_name" in det
            assert "confidence" in det
            assert "bbox" in det
            assert len(det["bbox"]) == 4

    def test_visualize(self):
        """测试结果可视化"""
        import numpy as np
        from algorithms.postprocess.visualize import draw_detections

        img = np.zeros((400, 400, 3), dtype=np.uint8)
        detections = [{
            "class_name": "crazing",
            "class_name_cn": "裂纹",
            "confidence": 0.85,
            "bbox": [50, 50, 100, 80],
            "area": 8000,
        }]
        result = draw_detections(img, detections)
        assert result.shape == img.shape
        assert result is not img  # 返回的是副本


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
