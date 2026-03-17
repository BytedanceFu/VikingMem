# 火山记忆库 Locomo 数据集测评指南
Python 版本：3.13

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 .env 文件

在项目根目录创建 `.env` 文件，配置以下环境变量：

```
AAKK="your_ak"
SSKK="your_sk"
MEMORY_API_KEY="your_memory_api_key"
ARK_API_KEY="your_ark_api_key"
```

说明：
- `AAKK` / `SSKK`：火山引擎 AK/SK，用于创建记忆库
- `MEMORY_API_KEY`：记忆库 API Key，用于记忆检索
- `ARK_API_KEY`：豆包 API Key，用于 LLM 推理

### 3. 配置模型 EP

在 `eval_utils/response_judge.py` 中修改模型 EP：

```python
model='ep-xxxxxxxxxxxxx',  # 修改为你的模型 EP
```

## 第一步：数据准备

### 1. 下载 Locomo 数据集

从 `https://github.com/snap-research/locomo/tree/main/data` 下载数据集文件，放置到项目的 `data` 目录下。

### 2. 数据格式转换

将 Locomo JSON 格式转换为记忆库适配的数据格式。

```bash
python convert_locomo_to_csv.py --input data/locomo10.json --output data/output.csv
```

## 第二步：创建记忆库

```bash
python create_memory_collection.py
```

## 第三步：数据导入

```bash
python import_data_to_memory.py
```

## 第四步：记忆检索与评测

```bash
python evaluate_locomo.py --csv data/query.csv 
```

可选参数：
- `--start`: 起始问题索引（从1开始）
- `--end`: 结束问题索引
- `--output`: 结果输出文件路径


