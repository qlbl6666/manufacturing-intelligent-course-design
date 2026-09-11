"""
文件处理工具
"""

import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename


def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def generate_unique_filename(original_filename):
    """生成唯一文件名，保留原始扩展名"""
    ext = Path(original_filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


def save_upload_file(file, upload_folder, allowed_extensions):
    """
    保存上传文件
    返回: (保存路径, 唯一文件名, 原始文件名)
    """
    if not file or file.filename == "":
        return None, None, None

    original_name = secure_filename(file.filename)
    if not allowed_file(original_name, allowed_extensions):
        return None, None, original_name

    unique_name = generate_unique_filename(original_name)
    save_path = os.path.join(upload_folder, unique_name)
    file.save(save_path)

    return save_path, unique_name, original_name
