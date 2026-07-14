# Aistock 功能说明文档

## 概述

Aistock 是一个 AI 驱动的 A 股市场数据管道，用于自动化收集、清洗、存储和管理股票市场数据。

## 核心功能

### 1. 多数据源支持

| 数据源 | 类型 | 特点 | 配置要求 |
|--------|------|------|----------|
| AkShare | 主力 | 免费、无需 token | 无 |
| Baostock | 备份 | 免费、稳定性好 | 无 |
| Tushare | 可选增强 | 需要 token | TUSHARE_TOKEN 环境变量 |

### 2. 自动降级链

```
AkShare (优先级 100) → Baostock (优先级 80) → Tushare (优先级 50)
```

当主数据源不可用时，自动切换到下一个数据源。

### 3. 数据清洗 (B 级基线)

| 清洗步骤 | 功能 | 说明 |
|----------|------|------|
| UniversalCleaner | 去重、空值处理、代码格式统一 | 000001 → 000001.SZ |
| AdjustmentCleaner | 前复权价格对齐 | 处理复权因子 |
| StatusCleaner | ST、停牌状态标记 | 自动识别 ST 股票 |
| OHLCValidator | OHLC 校验 | 检查 high≥low、价格非负 |
| ConvertibleBondCleaner | 可转债特定清洗 | 转股价值、溢价率计算 |
| FuturesCleaner | 期货特定清洗 | 主力合约、交割月标记 |
| OptionsCleaner | 期权特定清洗 | 实值/虚值、希腊字母 |
| QualityScorer | 数据质量评分 | 4 维度评分 (A/B/C/D) |

### 4. Parquet 存储

- **分区策略**: 按 asset_type / freq / year / month 分区
- **压缩算法**: 支持 zstd、snappy、gzip 等
- **增量更新**: 支持 upsert 按主键去重

### 5. 可观测性

- **结构化 JSON 日志**: 按天分区，支持 90 天留存
- **SQLite 任务追踪**: 记录每次运行的元数据
- **任务状态**: success / partial / failed

## 数据模型

### 支持的 Schema

| Schema | 用途 | 分区键 |
|--------|------|--------|
| StockDailySchema | 日线行情 | asset_type / year / month |
| StockMinuteSchema | 分钟线 | asset_type / frequency / year / month |
| FinanceSchema | 财务数据 | asset_type / report_period |
| NorthFlowSchema | 北向资金 | year / month |
| MarginTradeSchema | 融资融券 | year / month |
| AlternativeSchema | 另类数据 | sub_type / year / month |
| ReferenceSchema | 品种参考 | 无分区 |
| ConvertibleBondSchema | 可转债 | asset_type (cb) / year / month |
| FuturesSchema | 期货 | asset_type (future) / exchange / year / month |
| OptionsSchema | 期权 | asset_type (option) / underlying / option_type / year / month |

## CLI 命令

### fetch - 下载数据

```bash
python -m aistock.cli fetch \
  --asset-type stock \
  --schema daily \
  --codes "000001.SZ,600000.SH" \
  --start-date 2025-01-01 \
  --end-date 2025-01-31
```

**参数说明**:
- `--asset-type`: 资产类型 (stock/index/etf)
- `--schema`: 数据模型 (daily/minute/finance)
- `--codes`: 股票代码，逗号分隔（可选，默认全部）
- `--start-date`: 开始日期 (YYYY-MM-DD)
- `--end-date`: 结束日期（可选，默认今天）
- `--frequency`: 频率 (daily/1min/5min)

### update - 日更新

```bash
python -m aistock.cli update \
  --asset-type stock \
  --schema daily
```

自动查询已有数据的最新日期，增量下载并 upsert。

### status - 查看状态

```bash
python -m aistock.cli status
```

显示最近 10 个任务的运行状态。

## 配置文件

### pipeline.yaml

```yaml
data_dir: "data"              # 数据存储目录
log_dir: "logs"               # 日志目录

retry:
  max_attempts: 3             # 最大重试次数
  base_delay_s: 5.0           # 基础延迟（秒）
  backoff_multiplier: 2       # 退避倍数

timeout:
  source_request_s: 60        # 数据源请求超时
  pipeline_run_s: 600         # 管道运行超时

cleaner:
  profile: "baseline"         # 清洗级别 (baseline/advanced)

storage:
  backend: "parquet"          # 存储后端
  compression: "zstd"         # 压缩算法
  compression_level: 3        # 压缩级别

logging:
  dir: "logs"
  retention_days: 90          # 日志留存天数
```

### source_priority.yaml

```yaml
daily:
  - name: akstock
    priority: 100
    config: {}
  - name: baostock
    priority: 80
    config: {}
  - name: tushare
    priority: 50
    config:
      token: ${TUSHARE_TOKEN}

minute:
  - name: akstock
    priority: 100
  - name: tushare
    priority: 50

finance:
  - name: akstock
    priority: 100
  - name: tushare
    priority: 80
```

## 数据流

```
┌─────────────┐
│     CLI     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PipelineRunner│
└──────┬──────┘
       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
┌─────────────┐                        ┌─────────────┐
│ SourceRegistry│                       │   Cleaner   │
└──────┬──────┘                        └──────┬──────┘
       │                                      │
       ▼                                      ▼
┌─────────────┐                        ┌─────────────┐
│  SourceNode │                        │ STEPS       │
│  (AkStock/  │                        │ (Universal/ │
│   BaoStock/ │                        │  Adjustment/│
│   TuShare)  │                        │  Status/    │
└──────┬──────┘                        │  OHLC)      │
       │                               └──────┬──────┘
       │                                      │
       └──────────────────────────────────────┘
                        │
                        ▼
                ┌─────────────┐
                │StorageBackend│
                │  (Parquet)  │
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │  data/      │
                │  parquet/   │
                │  stock/     │
                │  daily/     │
                │  2025/01/   │
                └─────────────┘
```

## 错误处理

### 异常体系

```
PipelineError (基类)
├── SourceError
│   ├── SourceUnavailable (数据源不可达)
│   └── SourceRateLimited (数据源限速)
├── CleanError
│   └── ValidationError (校验失败)
└── StoreError
    ├── WriteError (写入失败)
    └── BackendUnavailable (后端不可达)
```

### 降级策略

1. **数据源不可达**: 跳过当前源，尝试下一个
2. **数据源限速**: 指数退避重试
3. **清洗失败**: 跳过当前源，尝试下一个
4. **存储失败**: 直接抛出异常（不降级）

## 测试覆盖

| 测试类别 | 数量 | 覆盖模块 |
|----------|------|----------|
| 单元测试 | 65 | 所有模块 |
| 集成测试 | 10 | Parquet 存储 |
| **总计** | **75** | **100% 通过** |

## 示例输出

```
Fetching daily data for stock...
Date range: 2025-01-01 to 2025-01-10

============================================================
Task ID: 7518038e-bbae-4906-9992-1ec3d7a645e3
Source: baostock
Status: partial
Records fetched: 7
Records after clean: 7
Records written: 7
Duration: 15803ms
Fallback used: baostock
Failed codes: 000001.SZ
============================================================
```

## 扩展指南

### 添加新数据源

1. 创建 `src/aistock/sources/newsource/` 目录
2. 实现 `client.py` - API 封装
3. 实现 `mapper.py` - 字段映射
4. 实现 `downloader.py` - 继承 SourceNode
5. 更新 `source_priority.yaml` 配置优先级

### 添加新清洗步骤

1. 创建 `src/aistock/cleaning/newstep.py`
2. 继承 `CleaningStep` 接口
3. 实现 `clean()` 和 `validate()` 方法
4. 添加到 `STEPS_BASELINE` 或 `STEPS_ADVANCED`

### 添加新 Schema

1. 创建 `src/aistock/schemas/newschema.py`
2. 定义 dataclass 字段
3. 实现 `validate()` 和 `partition_values()` 方法
4. 注册到 `SCHEMA_REGISTRY`
