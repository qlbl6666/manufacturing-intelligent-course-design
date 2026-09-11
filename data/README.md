# 数据目录说明

## 一、数据集来源

### 1.1 主数据集：NEU-DET 热轧钢带表面缺陷数据集

- **数据集名称**：NEU-DET (Northeastern University-DETection)
- **发布机构**：东北大学工业自动化实验室
- **下载地址**：https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database
- **备用地址**：https://github.com/abin24/Metal-Surface-Defect-Detection
- **数据规模**：1800 张灰度图像，分辨率 200×200 像素
- **缺陷类别**：6 类，每类 300 张
- **标注格式**：PASCAL VOC XML 格式（边界框标注）
- **许可协议**：学术研究免费使用

### 1.2 缺陷类别说明

| 类别编号 | 类别名称（英文） | 类别名称（中文） | 样本数量 | 说明 |
|---------|----------------|----------------|---------|------|
| 0 | crazing | 裂纹 | 300 | 表面网状裂纹 |
| 1 | inclusion | 夹杂 | 300 | 非金属夹杂物 |
| 2 | patches | 斑块 | 300 | 表面氧化斑块 |
| 3 | pitted_surface | 麻点 | 300 | 凹坑状表面缺陷 |
| 4 | rolled-in_scale | 氧化皮 | 300 | 轧制氧化皮 |
| 5 | scratches | 划痕 | 300 | 表面划痕 |

### 1.3 数据集目录结构（下载后）

```
data/
├── NEU-DET/
│   ├── IMAGES/              # 原始图片（1800张）
│   │   ├── crazing_1.jpg
│   │   ├── crazing_2.jpg
│   │   └── ...
│   └── ANNOTATIONS/         # XML标注文件
│       ├── crazing_1.xml
│       ├── crazing_2.xml
│       └── ...
├── processed/               # 预处理后的数据（脚本生成）
│   ├── images/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   └── labels/
│       ├── train/           # YOLO格式TXT标注
│       ├── val/
│       └── test/
├── preprocess.py            # 数据预处理脚本
├── dataset_index.csv        # 数据集索引
├── class_mapping.json       # 类别映射
└── README.md                # 本说明文件
```

> **注意**：由于数据集文件较大（约 50MB），未直接提交到仓库。请通过上述链接下载后解压到 `data/NEU-DET/` 目录下，然后运行 `preprocess.py` 进行预处理。

---

## 二、数据预处理

### 2.1 预处理流程

1. **数据清洗**：检查损坏图片、标注文件与图片的对应关系，移除不匹配的样本
2. **标注格式转换**：将 PASCAL VOC XML 格式转换为 YOLO TXT 格式（归一化坐标）
3. **数据集划分**：按 7:2:1 比例随机划分训练集、验证集、测试集（分层抽样，保证各类别比例一致）
4. **图像预处理**：
   - 尺寸归一化：统一调整为 640×640（YOLOv8 输入要求）
   - 像素归一化：像素值从 [0, 255] 归一化到 [0, 1]
   - 格式转换：统一为 RGB 三通道（原图为灰度图，复制为三通道）
5. **数据增强（训练时在线进行）**：
   - 随机水平翻转（概率 0.5）
   - 随机垂直翻转（概率 0.5）
   - 随机旋转（±15°）
   - 亮度扰动（±20%）
   - Mosaic 增强（YOLOv8 内置）

### 2.2 运行预处理脚本

```bash
cd data
python preprocess.py --source ./NEU-DET --output ./processed --ratio 7:2:1
```

### 2.3 预处理输出

- `processed/images/train/`：训练集图片（约 1260 张）
- `processed/images/val/`：验证集图片（约 360 张）
- `processed/images/test/`：测试集图片（约 180 张）
- `processed/labels/train/`：训练集 YOLO 格式标注
- `processed/labels/val/`：验证集 YOLO 格式标注
- `processed/labels/test/`：测试集 YOLO 格式标注
- `processed/dataset.yaml`：YOLOv8 训练配置文件

---

## 三、数据索引

详细的数据索引见 `dataset_index.csv`，包含每张图片的文件名、类别、划分集合、标注框数量等信息。

类别映射见 `class_mapping.json`。

---

## 四、数据统计

### 4.1 类别分布

| 缺陷类型 | 训练集 | 验证集 | 测试集 | 总计 |
|---------|--------|--------|--------|------|
| 裂纹 (crazing) | 210 | 60 | 30 | 300 |
| 夹杂 (inclusion) | 210 | 60 | 30 | 300 |
| 斑块 (patches) | 210 | 60 | 30 | 300 |
| 麻点 (pitted_surface) | 210 | 60 | 30 | 300 |
| 氧化皮 (rolled-in_scale) | 210 | 60 | 30 | 300 |
| 划痕 (scratches) | 210 | 60 | 30 | 300 |
| **合计** | **1260** | **360** | **180** | **1800** |

### 4.2 图像属性

- 原始分辨率：200×200 像素
- 预处理后分辨率：640×640 像素
- 颜色空间：灰度 → RGB（三通道复制）
- 文件格式：JPG
- 平均文件大小：约 25KB / 张

---

## 五、数据质量说明

- 所有图片均来自真实工业生产场景，具有实际业务意义
- 标注由专业人员完成，边界框准确
- 各类别样本数量均衡（每类 300 张），无严重类别不平衡问题
- 数据集中无重复图片
- 已验证所有标注文件与图片一一对应
