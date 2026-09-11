# AI 工具提示词记录目录

本目录保存课程设计过程中与 AI 编程工具交流的完整记录，用于 vibe coding 过程追溯。

## 记录文件列表

| 文件名 | 阶段 | 时间 | 主要内容 |
|--------|------|------|---------|
| session_001_topic_research.json | 第一阶段-选题调研 | 2026-09-10 | 选题方向讨论、数据集调研、vibe coding方法论学习 |
| session_002_solution_design.json | 第二阶段-方案设计 | 2026-09-11 | 系统架构设计、技术栈选型、检测流水线设计、数据预处理方案 |
| session_003_data_preprocessing.json | 第三阶段-数据准备 | 2026-09-11 | 预处理脚本开发、数据清洗逻辑、README文档结构 |

## 记录格式说明

每个 JSON 文件包含以下字段：
- `session_id`：会话唯一标识
- `timestamp`：会话时间
- `tool`：使用的 AI 工具
- `model`：使用的模型
- `phase`：所属课程设计阶段
- `conversations`：对话记录数组，每条包含 `role`（user/assistant）和 `content`
- `summary`：会话内容摘要

## 使用的 AI 工具

- **主要工具**：豆包 AI 编程助手（Doubao）
- **备选工具**：DeepSeek-Coder、Qwen Code
- **使用模型**：doubao-pro、DeepSeek-V4

## 更新说明

本目录将在课程设计的每个阶段同步更新，在上下文压缩前及时备份 prompt 记录并添加。后续开发阶段（系统开发、集成调试）的 AI 对话记录将持续追加。
