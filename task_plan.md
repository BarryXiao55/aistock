# Task Plan: aistock 项目骨架创建

## Goal
为 A 股数据管道项目创建完整的项目骨架，包括目录结构、配置文件、基础模块和测试框架。

## Current Phase
完成

## Phases

### Phase 1: 项目结构创建
- [x] 创建 pyproject.toml
- [x] 创建 src/aistock/ 包结构
- [x] 创建 config/ 目录和配置文件
- [x] 创建 tests/ 目录结构
- **Status:** complete

### Phase 2: 核心模块实现
- [x] exceptions.py - 异常体系
- [x] schemas/__init__.py - Schema 注册表
- [x] schemas/daily.py - StockDailySchema
- [x] schemas/minute.py - StockMinuteSchema
- [x] schemas/finance.py - FinanceSchema
- [x] schemas/alternative.py - 另类数据 Schema
- [x] schemas/reference.py - ReferenceSchema
- **Status:** complete

### Phase 3: 管道框架实现
- [x] pipeline/models.py - 数据模型
- [x] pipeline/source.py - SourceNode 接口
- [x] pipeline/cleaner.py - 清洗编排器
- [x] pipeline/runner.py - 管道运行器
- **Status:** complete

### Phase 4: 存储层实现
- [x] storage/interface.py - StorageBackend 接口
- [x] storage/query.py - QuerySpec 查询模型
- [x] storage/router.py - 后端路由
- [x] storage/parquet/__init__.py - 包初始化
- [x] storage/parquet/backend.py - Parquet 后端
- [x] storage/parquet/partition.py - 分区策略
- [x] tests/integration/test_parquet_backend.py - Parquet 测试
- **Status:** complete

### Phase 5: 清洗步骤实现
- [x] cleaning/interface.py - CleaningStep 接口
- [x] cleaning/universal.py - 通用清洗
- [x] cleaning/adjustment.py - 复权处理
- [x] cleaning/status.py - 状态标记
- [x] cleaning/validator.py - OHLC 校验
- [x] pipeline/cleaner.py - 更新 STEPS_BASELINE
- [x] tests/unit/test_cleaning_steps.py - 清洗步骤测试
- **Status:** complete

### Phase 6: 数据源插件
- [x] sources/registry.py - 注册表
- [x] sources/akstock/__init__.py - 包初始化
- [x] sources/akstock/client.py - AkShare API 客户端
- [x] sources/akstock/mapper.py - 数据映射
- [x] sources/akstock/downloader.py - AkStockSource 实现
- [x] sources/baostock/__init__.py - 包初始化
- [x] sources/baostock/client.py - Baostock API 客户端
- [x] sources/baostock/mapper.py - 数据映射
- [x] sources/baostock/downloader.py - BaoStockSource 实现
- [x] sources/tushare/__init__.py - 包初始化
- [x] sources/tushare/client.py - Tushare API 客户端
- [x] sources/tushare/mapper.py - 数据映射
- [x] sources/tushare/downloader.py - TuShareSource 实现
- [x] tests/unit/test_sources.py - 数据源测试
- **Status:** complete

### Phase 7: 可观测性
- [x] observability/models.py - 数据模型
- [x] observability/logger.py - 结构化日志
- [x] observability/tracer.py - 任务元数据
- [x] tests/unit/test_observability.py - 可观测性测试
- **Status:** complete

### Phase 8: CLI 入口
- [x] cli.py - Click CLI
- [x] tests/unit/test_cli.py - CLI 测试
- **Status:** complete

## Key Questions
1. 如何确保中断后可以恢复？(通过 progress.md 记录每一步)
2. 每个模块的依赖关系是什么？(exceptions -> schemas -> pipeline -> storage -> sources)

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 使用 uv 管理依赖 | 快速、现代的 Python 包管理器 |
| 使用 dataclass 定义 Schema | 简洁、类型安全 |
| 使用 ABC 定义接口 | 明确的抽象边界 |
| 使用 pytest 作为测试框架 | Python 生态标准 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |
