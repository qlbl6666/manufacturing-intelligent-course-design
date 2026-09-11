"""
结果可视化模块
在图像上绘制检测边界框、类别标签和置信度
"""

import cv2
import numpy as np

from config import Config


def draw_detections(image, detections, show_confidence=True, show_label=True):
    """
    在图像上绘制检测结果

    参数:
        image: BGR 图像 (numpy array)
        detections: 检测结果列表，每个元素包含 class_name, confidence, bbox:[x,y,w,h]
        show_confidence: 是否显示置信度
        show_label: 是否显示类别标签

    返回: 绘制后的图像
    """
    img = image.copy()

    for det in detections:
        class_name = det.get("class_name", "unknown")
        class_name_cn = det.get("class_name_cn", class_name)
        confidence = det.get("confidence", 0.0)
        bbox = det.get("bbox", [0, 0, 0, 0])
        x, y, w, h = bbox

        # 获取类别颜色
        color = Config.DEFECT_COLORS.get(class_name, (0, 255, 0))

        # 绘制边界框
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)

        # 绘制标签
        if show_label:
            label = class_name_cn
            if show_confidence:
                label = f"{class_name_cn} {confidence:.2f}"

            # 计算标签背景大小
            font_scale = 0.5
            thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
            )

            # 标签背景位置（在框上方，如果空间不够则在框内）
            label_y = y - text_h - baseline - 5
            if label_y < 0:
                label_y = y + text_h + 5

            # 绘制标签背景
            cv2.rectangle(
                img,
                (x, label_y - text_h - baseline),
                (x + text_w + 10, label_y + baseline),
                color,
                -1,
            )
            # 绘制标签文字
            cv2.putText(
                img,
                label,
                (x + 5, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA,
            )

    return img


def draw_classification_result(image, class_name_cn, probabilities, classes):
    """
    绘制分类结果（快速模式）
    在图像右上角显示分类结果和概率条形图
    """
    img = image.copy()
    h, w = img.shape[:2]

    # 半透明背景面板
    panel_w = 220
    panel_h = 30 + len(classes) * 22
    panel_x = w - panel_w - 10
    panel_y = 10

    overlay = img.copy()
    cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)

    # 标题
    cv2.putText(img, "分类结果", (panel_x + 10, panel_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    # 各类别概率条
    for i, cls in enumerate(classes):
        prob = probabilities.get(cls, 0)
        bar_y = panel_y + 35 + i * 22
        cls_cn = Config.DEFECT_CLASSES_CN.get(cls, cls)

        # 类别名
        cv2.putText(img, cls_cn, (panel_x + 10, bar_y + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)

        # 概率条背景
        bar_x = panel_x + 70
        bar_w = 130
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_w, bar_y + 12), (80, 80, 80), -1)

        # 概率条填充
        fill_w = int(bar_w * prob)
        color = Config.DEFECT_COLORS.get(cls, (0, 255, 0))
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + fill_w, bar_y + 12), color, -1)

        # 概率值
        cv2.putText(img, f"{prob:.2f}", (bar_x + bar_w + 5, bar_y + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1, cv2.LINE_AA)

    return img


def save_result_image(image, save_path):
    """保存结果图像"""
    cv2.imwrite(str(save_path), image)
    return save_path
