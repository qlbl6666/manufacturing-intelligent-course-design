# manufacturing-intelligent-course-design
## 二、数据准备阶段
### 1. 数据来源
本项目使用自建模拟文本分类数据集，原始数据存放在 `data/raw/` 目录下。
数据集共1000条样本，包含序号、文本内容、分类标签3个字段，共4个分类。

### 2. 数据预处理
- 处理步骤：数据去重、缺失值清理
- 代码位置：`scripts/generate_data.py`（生成原始数据）、`scripts/preprocess.py`（数据预处理）
- 处理后数据：存放在 `data/processed/` 目录下

### 3. AI工具对话记录
本阶段与AI工具的全部交互记录，已备份在 `prompt/data_preparation_prompts.json` 文件中。
