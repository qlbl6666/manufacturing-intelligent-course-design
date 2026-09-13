# 基于深度学习的工业产品表面缺陷智能检测系统

> 制造智能技术课程设计项目

## 项目简介

本项目是面向制造/工业场景的智能应用，运用 vibe coding 方法开发一个 **B/S + C/S 双架构** 的工业产品表面缺陷智能检测系统。用户可通过浏览器（B/S 端）或桌面客户端（C/S 端）上传工业产品表面图片，系统自动调用深度学习模型进行缺陷识别与定位，实现制造环节质量检测的智能化。

## 课程设计信息

- **课程名称**：制造智能技术
- **项目题目**：基于深度学习的工业产品表面缺陷智能检测系统
- **开发方法**：Vibe Coding（AI 辅助编程）
- **系统架构**：B/S + C/S 双架构（浏览器/服务器 + 桌面客户端/服务器）

## 技术方向

本项目涉及《制造智能技术基础》课程的 4 个技术方向：

| 序号 | 技术方向 | 在系统中的应用 |
|------|---------|--------------|
| 1 | 深度学习与卷积神经网络 | ResNet50 缺陷分类、YOLOv8 缺陷检测 |
| 2 | 计算机视觉与图像处理 | 图像预处理、数据增强、结果可视化 |
| 3 | 机器学习与模式识别 | 模型训练、评估、超参数优化 |
| 4 | 智能制造系统与架构 | B/S + C/S 双架构设计、RESTful API 接口、桌面客户端、流程集成 |

## 技术栈

### 前端（B/S 端）
- HTML5 + CSS3 + JavaScript (ES6+)
- Bootstrap 5（UI 组件库）
- ECharts（数据可视化）
- Axios（HTTP 请求）

### 桌面客户端（C/S 端）
- Python Tkinter（GUI 框架，标准库内置）
- requests（HTTP 请求，调用后端 API）
- Pillow（图片显示）
- ttk（表格、标签页组件）

### 后端
- Python 3.10 + Flask（Web 框架）
- PyTorch + torchvision（深度学习）
- Ultralytics YOLOv8（目标检测）
- OpenCV + Pillow（图像处理）
- SQLite + SQLAlchemy（数据库）

### 开发工具
- Git + GitHub（版本控制）
- 豆包 AI 编程助手（Vibe Coding）

## 项目结构

```
manufacturing-intelligent-course-design/
├── 学习笔记.md              # 第一阶段：AI工具学习、Git原理、选题调研
├── 选题说明.md              # 第二阶段：选题、目标、技术方向映射
├── 方案设计.md              # 第二阶段：需求分析、方案论证、技术路线
├── README.md                # 项目说明（本文件）
├── requirements.txt         # Python 依赖
├── .gitignore               # Git 忽略配置
├── data/                    # 第三阶段：数据目录
│   ├── README.md            # 数据来源与预处理说明
│   ├── preprocess.py        # 数据预处理脚本
│   ├── dataset_index.csv    # 数据集索引
│   ├── class_mapping.json   # 类别映射
│   ├── NEU-DET/             # 原始数据集（需自行下载）
│   └── processed/           # 预处理后的数据（脚本生成）
├── prompt/                  # AI 工具提示词记录
│   ├── README.md            # 记录说明
│   ├── session_001_topic_research.json
│   ├── session_002_solution_design.json
│   └── session_003_data_preprocessing.json
├── src/                     # 源代码目录（B/S 端）
│   ├── app.py               # Flask 应用入口
│   ├── config.py            # 配置文件
│   ├── models/              # 数据库模型
│   ├── routes/              # API 路由
│   ├── algorithms/          # 算法模块
│   │   ├── preprocess/      # 图像预处理
│   │   ├── models/          # 模型定义
│   │   ├── inference/       # 推理引擎
│   │   └── postprocess/     # 后处理与可视化
│   ├── templates/           # HTML 模板
│   └── static/              # 前端静态资源
│       ├── css/
│       ├── js/
│       └── images/
├── client/                  # C/S 桌面客户端
│   ├── desktop_client.py    # Tkinter 桌面客户端主程序
│   └── 启动客户端.bat        # 客户端启动脚本
├── tests/                   # 自动化测试
├── test_images/             # 测试用缺陷图片（6类）
└── docs/                    # 设计文档
    ├── 需求规格说明书.md
    ├── 设计报告.md
    ├── 答辩PPT.pptx
    └── 演示视频.mp4
```

## 数据集

### 数据集来源

本项目使用 **NEU-DET 热轧钢带表面缺陷数据集**：

- **发布机构**：东北大学工业自动化实验室
- **下载地址**：https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database
- **数据规模**：1800 张灰度图像（200×200），6 类缺陷，每类 300 张
- **标注格式**：PASCAL VOC XML（边界框标注）
- **缺陷类别**：裂纹(crazing)、夹杂(inclusion)、斑块(patches)、麻点(pitted_surface)、氧化皮(rolled-in_scale)、划痕(scratches)

### 数据预处理

由于数据集文件较大，未直接提交到仓库。请按以下步骤准备数据：

```bash
# 1. 下载数据集并解压到 data/NEU-DET/ 目录
# 目录结构应为：
#   data/NEU-DET/IMAGES/     (图片)
#   data/NEU-DET/ANNOTATIONS/ (XML标注)

# 2. 运行预处理脚本
cd data
python preprocess.py --source ./NEU-DET --output ./processed --ratio 7:2:1 --img-size 640
```

预处理完成后将生成：
- `processed/images/{train,val,test}/` — 划分后的图片
- `processed/labels/{train,val,test}/` — YOLO 格式标注
- `processed/dataset.yaml` — YOLOv8 训练配置

详细说明请参考 [data/README.md](data/README.md)。

## 快速开始

### 环境配置

```bash
# 克隆仓库
git clone https://github.com/qlbl6666/manufacturing-intelligent-course-design.git
cd manufacturing-intelligent-course-design

# 创建虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 数据准备

按照上述「数据集」部分下载 NEU-DET 数据集并运行预处理脚本。

### 模型训练（可选，使用预训练模型可跳过）

```bash
# YOLOv8 检测模型训练
yolo train data=data/processed/dataset.yaml model=yolov8s.pt epochs=100 imgsz=640 batch=16

# ResNet50 分类模型训练
python src/algorithms/train_classifier.py
```

### 启动系统

#### B/S 端（Web 浏览器）

```bash
python src/app.py
```

启动后浏览器访问 `http://localhost:5000`，默认账号 `admin / admin123`。

#### C/S 端（桌面客户端）

```bash
# 先启动后端服务
python src/app.py

# 再启动桌面客户端（另开一个终端）
python client/desktop_client.py
```

或 Windows 下直接双击 `client/启动客户端.bat`。

> 注意：C/S 客户端需要后端服务先启动，客户端通过 RESTful API 与后端通信。

打开浏览器访问：http://localhost:5000

## 功能特性

- **图像上传检测**：支持 JPG/PNG/BMP 格式，单张 ≤ 10MB
- **双模式检测**：快速模式（仅分类）/ 精确模式（分类+定位）
- **结果可视化**：边界框标注、缺陷类型、置信度显示
- **历史记录**：检测记录查询、筛选、详情查看
- **报告导出**：检测结果导出为 PDF/Excel
- **统计仪表盘**：检测量趋势、缺陷类型分布
- **模型管理**：模型版本切换、检测阈值配置（管理员）

## 课程设计进度

| 阶段 | 时间 | 任务 | 状态 |
|------|------|------|------|
| 第一阶段 | D1-D2 | 工具配置、vibe coding 学习、选题调研 | ✅ 完成 |
| 第二阶段 | D3-D5 | 选题说明、方案设计 | ✅ 完成 |
| 第三阶段 | D6 | 数据资源整理、预处理 | ✅ 完成 |
| 第四阶段 | D7-D8 | 系统详细开发 | 🔄 进行中 |
| 第五阶段 | D9 | 集成调试、报告撰写 | ⏳ 待开始 |
| 第六阶段 | D10 | 答辩 | ⏳ 待开始 |

## AI 工具使用披露

本项目全程使用 AI 编程工具辅助开发（Vibe Coding 方法）：

- **主要工具**：豆包 AI 编程助手
- **使用模型**：doubao-pro、DeepSeek-V4
- **使用范围**：代码生成、调试辅助、文档撰写、方案设计
- **提示词记录**：完整的 AI 对话记录保存在 [prompt/](prompt/) 目录
- **人工审查**：所有 AI 生成代码均经过人工审查和理解，关键逻辑已验证

## 参考文献

1. 张智海等. 制造智能技术基础[M]. 北京: 清华大学出版社, 2022.
2. He K, Zhang X, Ren S, et al. Deep Residual Learning for Image Recognition[C]//CVPR, 2016.
3. Jocher G, et al. Ultralytics YOLOv8[EB/OL]. https://github.com/ultralytics/ultralytics, 2023.
4. He Y, et al. An End-to-end Steel Surface Defect Detection Approach[J]. IEEE TIM, 2020.

## 许可证

本项目仅用于课程设计学习用途。
