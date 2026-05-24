# Aistock 数据管道设计文档

**日期**: 2026-05-24
**状态**: 待审核
**范围**: Phase 1 — 本地数据源建设

---

## 1. 目标与范围

建立 A 股市场的本地标准化数据源，支撑后续 AI 挖掘和回测需求。本阶段专注于：

- 三大免费数据源（AkShare、Baostock、Tushare）的接入与降级
- 历史数据一次性下载 + 日更新
- B 级数据清洗（去重/空值/复权/停牌标记）
- 标准化 Parquet 存储
- 结构化可追溯日志

## 2. 核心决策汇总

| 维度 | 决策 |
|------|------|
| 品种范围 | 全品种（股票 + 指数 + ETF + 可转债 + 期货 + 期权） |
| 频率 | 日线优先，分钟/分笔按需配置 |
| 字段 | 行情 + 全量财务 + 另类数据 |
| 历史回溯 | 近 10 年 |
| 存储格式 | Parquet 列式文件（后期可扩展 PostgreSQL） |
| 数据源策略 | AkShare 主力 -> Baostock 备份行情 -> Tushare 可选增强 |
| 更新机制 | 手动触发 -> 日调度器 -> 按需扩展周/月/季 |
| 清洗标准 | B 级基线（去重 + 空值 + 前复权对齐 + 停牌标记）+ 预留 C 级扩展 |
| 行业标准 | 先桌面调研 -> B 实施 -> 预留观测点 |
| 可观测性 | 结构化 JSON 日志 + SQLite 任务元数据 |

## 3. 项目目录结构

```
aistock/
├── .gitignore                          # Git 忽略规则
├── CLAUDE.md                          # 项目指导文档
├── pyproject.toml                     # uv 项目配置 + 依赖
├── README.md                          # 项目概述
│
├── config/                            # 配置文件（YAML）
│   ├── instruments.yaml               #   品种清单（股票/指数/ETF/可转债/期货/期权）
│   ├── source_priority.yaml           #   数据源优先级 & fallback 链
│   └── pipeline.yaml                  #   运行参数（超时/重试/路径/压缩）
│
├── src/aistock/                       # 主包
│   ├── __init__.py
│   ├── exceptions.py                  # 统一异常体系
│   │
│   ├── schemas/                       # 内部标准数据模型
│   │   ├── __init__.py                #   SCHEMA_REGISTRY 映射表
│   │   ├── daily.py                   #   StockDailySchema (OHLCV + 复权 + 状态)
│   │   ├── minute.py                  #   StockMinuteSchema
│   │   ├── finance.py                 #   FinanceSchema (三表 + 财务指标)
│   │   ├── alternative.py             #   AlternativeSchema + NorthFlowSchema + MarginTradeSchema
│   │   └── reference.py               #   ReferenceSchema (股票基本信息/行业分类)
│   │
│   ├── pipeline/                      # 管道框架（三阶段接口）
│   │   ├── __init__.py
│   │   ├── models.py                  #   FetchSpec / PipelineContext / PipelineReport / WriteResult
│   │   ├── source.py                  #   SourceNode 抽象接口
│   │   ├── cleaner.py                 #   Cleaner 编排器
│   │   └── runner.py                  #   PipelineRunner 编排器（含降级链）
│   │
│   ├── sources/                       # 数据源插件（每个源一个子包）
│   │   ├── __init__.py
│   │   ├── registry.py                #   插件注册表 + 优先级加载
│   │   ├── akstock/
│   │   │   ├── __init__.py
│   │   │   ├── client.py              #     akshare API 封装 + 限速/重试
│   │   │   ├── downloader.py          #     实现 SourceNode
│   │   │   └── mapper.py              #     字段 -> 内部 Schema
│   │   ├── baostock/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── downloader.py
│   │   │   └── mapper.py
│   │   └── tushare/
│   │       ├── __init__.py
│   │       ├── client.py
│   │       ├── downloader.py
│   │       └── mapper.py
│   │
│   ├── cleaning/                      # 清洗 & 标准化
│   │   ├── __init__.py
│   │   ├── interface.py               #   CleaningStep 抽象接口
│   │   ├── registry.py                #   清洗步骤链，按序执行
│   │   ├── universal.py               #   通用清洗（去重/空值/代码格式统一）
│   │   ├── adjustment.py              #   复权处理（前复权对齐）
│   │   ├── status.py                  #   交易状态标记（停牌/退市/ST）
│   │   ├── validator.py               #   基础校验（OHLC高低校验/量价非负）
│   │   ├── cross_validator.py         #   跨源交叉验证（C 级预留）
│   │   └── quality.py                 #   数据质量评分（C 级预留）
│   │
│   ├── storage/                       # 存储抽象 + 多后端
│   │   ├── __init__.py
│   │   ├── interface.py               #   StorageBackend 抽象 (write/read/query/upsert/exists)
│   │   ├── router.py                  #   根据配置路由到后端
│   │   ├── query.py                   #   QuerySpec 查询模型
│   │   ├── parquet/                    #   Parquet 后端 (Phase 1 实现)
│   │   │   ├── __init__.py
│   │   │   ├── backend.py             #     ParquetBackend 完整实现
│   │   │   └── partition.py           #     分区策略 (asset_type/freq/year/month/)
│   │   └── postgres/                  #   PostgreSQL 后端 (Phase 2 骨架)
│   │       ├── __init__.py
│   │       ├── backend.py             #     PostgresBackend (后期实现)
│   │       └── models.py              #     SQLAlchemy ORM (复用 schemas 定义)
│   │
│   ├── factors/                       # 因子计算层（骨架预留）
│   │   ├── __init__.py
│   │   ├── interface.py               #   FactorCalculator 抽象
│   │   └── registry.py                #   因子注册（空清单，逐步填充）
│   │
│   ├── observability/                 # 可观测性
│   │   ├── __init__.py
│   │   ├── logger.py                  #   结构化 JSON 日志
│   │   ├── tracer.py                  #   任务元数据记录 (SQLite)
│   │   └── models.py                  #   TaskRun / DataRecord SQLite 模型
│   │
│   └── cli.py                         # 统一 CLI 入口 (click)
│
├── notebooks/                         # Jupyter 数据探索
│   ├── 01_source_exploration/         #   各数据源 API 探索
│   ├── 02_data_profile/               #   原始数据分布/边界分析
│   └── 03_cleaning_validation/        #   清洗规则验证
│
├── scripts/                           # 持久化临时脚本
│   ├── exploration/                   #   数据源探索/字段对比
│   ├── backfill/                      #   历史数据一次性回填
│   ├── debug/                         #   问题复现/修复
│   └── migration/                     #   Schema 变更数据迁移
│
├── artifacts/                         # 持久文档（设计/决策/调研/变更/复盘）
│   ├── specs/                         #   设计规格文档
│   │   └── data-pipeline-design.md    #     管道设计文档（本文档）
│   ├── adr/                           #   架构决策记录 (编号递增)
│   │   └── .gitkeep
│   ├── research/                      #   调研报告
│   │   ├── data-source-research.md    #     三大数据源能力/限制调研
│   │   └── industry-data-standards.md #     金融数据行业标准调研
│   ├── changelogs/                    #   设计变更记录
│   │   └── .gitkeep
│   └── postmortems/                   #   Bug 复盘 / 根因分析
│       └── .gitkeep
│
├── tests/                             # 测试
│   ├── conftest.py                    #   共享 fixture（PipelineContext mock/sample DataFrames）
│   ├── unit/                          #   单元测试（Schema/CleaningStep/SourceRegistry/异常）
│   ├── integration/                   #   集成测试（Parquet往返/降级链/CLI/全链路）
│   └── fixtures/                      #   测试固件
│       ├── sample_daily_good.parquet  #     合法日线（5只×5天）
│       ├── sample_daily_bad.csv       #     含脏数据（缺列/负价/倒挂）
│       ├── sample_finance.csv         #     合法财务数据
│       └── mock_responses/            #     API 模拟响应 JSON
│
├── data/                              # 本地数据 (gitignore)
│   ├── raw/                           #   原始下载缓存
│   ├── parquet/                       #   标准化 Parquet
│   └── meta/                          #   data_pipeline.db (SQLite)
│
└── logs/                              # 结构化日志 (gitignore)
```

### 分层依赖规则

```
CLI -> PipelineRunner -> SourceNode -> Cleaner -> StorageBackend
                            |             |           |
                       observability    schemas     config
```

- **上层只依赖抽象**：`pipeline/runner.py` 依赖 `StorageBackend` 接口，`storage/router.py` 负责实例化，不感知 Parquet/PostgreSQL
- **横向隔离**：三个数据源子包互不引用，通过 `sources/registry.py` 统一注册
- **schemas 是纵向枢纽**：mapper->schemas、cleaner->schemas、storage->schemas，全部对齐

---

## 4. 核心接口定义

### 4.1 数据模型 (pipeline/models.py)

```python
from dataclasses import dataclass
from datetime import date
from logging import Logger

@dataclass
class FetchSpec:
    """一次数据抓取的规格"""
    asset_type: str           # "stock" | "index" | "etf" | "cb" | "future" | "option"
    codes: list[str] | None   # None = 全部品种
    start_date: date
    end_date: date
    schema: type              # StockDailySchema | StockMinuteSchema | ...
    frequency: str = "daily"  # "daily" | "1min" | "5min" | "15min" | "30min" | "60min"

@dataclass
class PipelineContext:
    """贯穿一次管道运行的上下文"""
    task_id: str              # UUID，贯穿全链路日志
    config: dict              # pipeline.yaml 配置快照
    log: Logger               # 结构化 logger

@dataclass
class WriteResult:
    """存储写入结果"""
    records_written: int
    partitions_affected: list[str]
    backend: str              # "parquet" | "postgres"

@dataclass
class PipelineReport:
    """一次管道运行的完整报告"""
    task_id: str
    source_name: str
    status: str               # "success" | "partial" | "failed"
    records_fetched: int
    records_after_clean: int
    records_written: int
    duration_ms: int
    issues: list[str]         # 清洗/校验中发现的问题
    failed_codes: list[str]   # 下载/清洗失败的品种代码
    fallback_used: str | None # 降级到了哪个源
```

### 4.2 SourceNode 接口 (pipeline/source.py)

```python
from abc import ABC, abstractmethod

class SourceNode(ABC):
    """数据源抽象 --- 每个数据源插件实现此接口"""
    name: str                              # "akstock" | "baostock" | "tushare"
    retry_max: int = 3
    retry_delay_s: float = 5.0

    @abstractmethod
    def supports(self, asset_type: str, schema: type) -> bool:
        """声明能力：该源是否支持此品种+数据模型"""
        ...

    @abstractmethod
    def fetch(self, spec: FetchSpec) -> pd.DataFrame:
        """
        执行下载，返回与内部 Schema 字段对齐的 DataFrame。
        实现分为 client.py（API 调用 + 限速重试）和 downloader.py（调用 client + mapper）。
        """
        ...

    def fetch_with_retry(self, spec: FetchSpec) -> pd.DataFrame:
        """基类提供重试模板，子类可覆盖"""
        last_exc = None
        for attempt in range(self.retry_max):
            try:
                return self.fetch(spec)
            except SourceRateLimited as e:
                time.sleep(self.retry_delay_s * (2 ** attempt))
                last_exc = e
            except SourceUnavailable:
                raise  # 不可达不重试，交给 Runner 降级
        raise last_exc

    def check_health(self) -> bool:
        """健康检查：数据源当前是否可连通"""
        return True
```

### 4.3 CleaningStep 接口 (cleaning/interface.py)

```python
from abc import ABC, abstractmethod

class CleaningStep(ABC):
    """清洗步骤抽象 --- 一个步骤做一件事"""
    name: str                          # 步骤名称，用于日志/追溯
    requires: list[str] = []           # 前置步骤声明

    @abstractmethod
    def clean(self, df: pd.DataFrame, ctx: PipelineContext) -> pd.DataFrame:
        """执行清洗，返回处理后的 DataFrame"""
        ...

    def validate(self, df: pd.DataFrame) -> list[str]:
        """后置校验，返回问题描述列表（空列表 = 通过）"""
        return []
```

### 4.4 Cleaner 编排器 (pipeline/cleaner.py)

`pipeline/cleaner.py` 负责串联清洗步骤，`cleaning/` 下各文件是具体步骤的实现。二者是编排器与步骤的关系。

```python
class Cleaner:
    """清洗编排器 --- 按注册顺序串联执行"""
    def __init__(self, steps: list[CleaningStep]):
        self._steps = steps

    def clean(self, df: pd.DataFrame, ctx: PipelineContext) -> tuple[pd.DataFrame, list[str]]:
        """依次执行所有步骤，返回 (清洗后DataFrame, 问题列表)"""
        issues = []
        for step in self._steps:
            try:
                df = step.clean(df, ctx)
                step_issues = step.validate(df)
                issues.extend(f"[{step.name}] {i}" for i in step_issues)
            except CleanError as e:
                ctx.log.error(f"cleaning step [{step.name}] failed: {e}")
                raise
        return df, issues

# 注册链（配置化选择 B 级或 C 级）
STEPS_BASELINE = [
    UniversalCleaner(),      # 1. 去重 + 空值 + 代码格式统一
    AdjustmentCleaner(),     # 2. 复权处理（依赖步骤1的代码格式统一）
    StatusCleaner(),         # 3. 停牌/退市/ST 标记
    OHLCValidator(),         # 4. 基础 OHLC 校验
]

STEPS_ADVANCED = STEPS_BASELINE + [
    CrossValidator(),        # 5. 跨源交叉验证（C 级）
    QualityScorer(),         # 6. 数据质量评分（C 级）
]
```

### 4.5 StorageBackend 接口 (storage/interface.py)

```python
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """存储后端抽象"""
    name: str                             # "parquet" | "postgres"

    @abstractmethod
    def write(self, df: pd.DataFrame, schema: type,
              partition_keys: dict) -> WriteResult:
        """全量写入，覆盖已有分区"""
        ...

    @abstractmethod
    def read(self, query: QuerySpec) -> pd.DataFrame:
        """按条件读取"""
        ...

    @abstractmethod
    def upsert(self, df: pd.DataFrame, schema: type,
               partition_keys: dict, on_conflict: list[str]) -> WriteResult:
        """按主键去重更新（如 trade_date + code），日更新用"""
        ...

    @abstractmethod
    def exists(self, schema: type, partition_keys: dict) -> bool:
        """检查指定分区是否已有数据，避免重复下载"""
        ...
```

### 4.5.1 QuerySpec 查询模型 (storage/query.py)

```python
@dataclass
class QuerySpec:
    """跨后端统一查询规格 --- 屏蔽 Parquet/SQL 差异"""
    schema: type                      # Schema 类
    asset_types: list[str] | None = None
    codes: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None
    frequency: str | None = None      # 分钟线时指定
    columns: list[str] | None = None  # None = 全部列
    partition_keys: dict | None = None # 精确分区命中
```

### 4.6 PipelineRunner 编排器 (pipeline/runner.py)

```python
class PipelineRunner:
    """执行一次管道任务，负责 Source->Clean->Store 全链路编排 + 降级"""

    def __init__(self, registry: SourceRegistry, cleaner: Cleaner,
                 store: StorageBackend, ctx: PipelineContext):
        self._registry = registry
        self._cleaner = cleaner
        self._store = store
        self._ctx = ctx

    def run(self, spec: FetchSpec) -> PipelineReport:
        """
        降级链（含 CleanError 降级）:
          akstock.fetch() -> 成功 -> cleaner -> store
                        -> 失败（源不可达/限速/清洗失败）-> baostock.fetch()
                                                       -> 成功 -> cleaner -> store
                                                       -> 失败 -> tushare.fetch()
                                                             -> success/partial/failed

        StoreError 不降级（存储后端是共享的，切源无意义）。
        Partial: 成功的数据正常写入，失败的 codes 记录到 report.failed_codes。
        """
        issues_overall = []
        start_time = time.monotonic()

        for source in self._registry.get_all(spec.asset_type, spec.schema):
            try:
                if not source.check_health():
                    self._ctx.log.info(f"source [{source.name}] unhealthy, skipping")
                    continue

                # 1. Fetch —— 立即捕获原始行数
                df = source.fetch_with_retry(spec)
                records_fetched = len(df)

                # 2. Schema 边界校验 —— 过滤不可修复的脏行（如 high<low、价格为负）
                #    校验 _不通过的行直接丢弃_，不传播到下游
                schema_issues = spec.schema.validate(df)
                if schema_issues:
                    self._ctx.log.warning(f"schema validation: {schema_issues}")
                    issues_overall.extend(schema_issues)
                    before = len(df)
                    df = df[~self._find_invalid_rows_mask(df, spec.schema)]
                    self._ctx.log.info(
                        f"filtered {before - len(df)} invalid rows from {before}")

                # 3. Clean（含清洗失败 -> 降级到下个源）
                df, clean_issues = self._cleaner.clean(df, self._ctx)
                issues_overall.extend(clean_issues)

                # 4. Write
                result = self._store.write(df, spec.schema, spec.schema.partition_values(df))

                # 5. 判断成功/部分成功
                #    如果 spec.codes 指定了具体品种列表，对比请求集与结果集
                #    如果 codes=None（下载全部），以是否有数据产出为判断依据
                if spec.codes is not None:
                    requested = set(spec.codes)
                    actual = set(df["code"].unique())
                    failed_codes = sorted(requested - actual)
                else:
                    failed_codes = []

                if records_fetched == 0:
                    status = "failed"
                elif len(failed_codes) > 0:
                    status = "partial"
                else:
                    status = "success"

                return PipelineReport(
                    task_id=self._ctx.task_id,
                    source_name=source.name,
                    status=status,
                    records_fetched=records_fetched,
                    records_after_clean=len(df),
                    records_written=result.records_written,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                    issues=issues_overall,
                    failed_codes=failed_codes,
                    fallback_used=(source.name if source != self._registry.primary else None)
                )

            except (SourceUnavailable, SourceRateLimited, CleanError) as e:
                self._ctx.log.warning(f"source [{source.name}] failed: {e}, falling back")
                continue
            except StoreError:
                raise  # 存储层失败不降级，直接抛

        raise PipelineError("All sources exhausted --- unable to fetch data")
```

`_find_invalid_rows_mask` 为私有辅助方法，根据 Schema 校验规则定位脏行（布尔 mask）；`partition_values(df)` 是每个 Schema 的类方法，从数据列推导分区路径。

### 4.7 统一异常体系 (exceptions.py)

```python
class PipelineError(Exception):
    """管道异常基类"""
    pass

class SourceError(PipelineError):
    """数据源层异常"""
    pass

class SourceUnavailable(SourceError):
    """数据源不可达"""
    pass

class SourceRateLimited(SourceError):
    """数据源触发限速"""
    pass

class CleanError(PipelineError):
    """清洗层异常"""
    pass

class ValidationError(CleanError):
    """校验未通过"""
    pass

class StoreError(PipelineError):
    """存储层异常"""
    pass

class WriteError(StoreError):
    """写入失败"""
    pass

class BackendUnavailable(StoreError):
    """存储后端不可达"""
    pass
```

### 4.8 存储后端路由 (storage/router.py)

```python
def get_backend(config: dict) -> StorageBackend:
    """根据 pipeline.yaml 中 storage.backend 字段创建后端实例"""
    backend_name = config["storage"]["backend"]   # "parquet" | "postgres"
    if backend_name == "parquet":
        from aistock.storage.parquet.backend import ParquetBackend
        return ParquetBackend(config)
    if backend_name == "postgres":
        from aistock.storage.postgres.backend import PostgresBackend  # Phase 2
        return PostgresBackend(config)
    raise StoreError(f"Unknown backend: {backend_name}")
```

CLI/Runner 启动时调用一次 `get_backend()`，之后全程面向 `StorageBackend` 接口编程。

---

## 5. 内部标准 Schema

### 5.1 StockDailySchema（日线行情）

```python
@dataclass
class StockDailySchema:
    asset_type:   str          # "stock" | "index" | "etf" | "cb" | "future" | "option"
    code:         str          # 内部统一代码: "000001.SZ" / "600000.SH"
    trade_date:   date         # 交易日 YYYY-MM-DD
    open:         float64
    high:         float64
    low:          float64
    close:        float64
    volume:       int64        # 成交量（股）
    amount:       float64      # 成交额（元）
    turnover:     float32      # 换手率（0-1，可为 NA）
    adj_factor:   float64      # 前复权因子（默认前复权）
    is_st:        bool         # 是否 ST
    is_suspended: bool         # 是否停牌
```

### 5.2 StockMinuteSchema（分钟线）

```python
@dataclass
class StockMinuteSchema:
    asset_type:   str
    code:         str
    trade_time:   datetime     # "2025-01-06 09:35:00"
    frequency:    str          # "1min" | "5min" | "15min" | "30min" | "60min"
    open:         float64
    high:         float64
    low:          float64
    close:        float64
    volume:       int64
    amount:       float64
```

### 5.3 FinanceSchema（财务数据）

```python
@dataclass
class FinanceSchema:
    code:              str
    report_period:     str          # "2025Q4" | "2025H2" | "2025A"
    report_type:       str          # "q" | "h" | "a"
    pub_date:          date
    total_assets:      float64      # 资产负债表
    total_liabilities: float64
    shareholders_equity: float64
    revenue:           float64      # 利润表
    net_profit:        float64
    eps:               float64      # 关键指标
    bps:               float64
    roe:               float32
    pe_ttm:            float32
    pb:                float32

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        issues = []
        required = {"code", "report_period", "pub_date", "total_assets",
                    "shareholders_equity", "revenue", "net_profit", "eps"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
        if (df["total_assets"] < 0).any():
            issues.append("Negative total_assets")
        if (df["revenue"] < 0).any():
            issues.append("Negative revenue")  # 营收可为负（退市边缘），仅标记
        if (df["report_period"].str.match(r"^\d{4}Q[1-4]$")).all() is False:
            issues.append("Invalid report_period format")
        return issues
```

### 5.4 另类数据（分级 Schema）

高频使用且字段固定的另类数据用**具体 Schema**（保留列式查询性能），字段不定或低频的用 **JSON Schema**（灵活性兜底）。

#### 5.4.1 具体 Schema（高频子类型，列式存储）

```python
@dataclass
class NorthFlowSchema:
    """北向资金"""
    code:        str
    trade_date:  date
    buy_amount:  float64   # 买入额（元）
    sell_amount: float64   # 卖出额（元）
    net_flow:    float64   # 净流入

@dataclass
class MarginTradeSchema:
    """融资融券"""
    code:           str
    trade_date:     date
    margin_buy:     float64  # 融资买入额
    margin_balance: float64  # 融资余额
    short_sell:     float64  # 融券卖出量
    short_balance:  float64  # 融券余量
```

#### 5.4.2 通用 Schema（低频/字段不定，JSON 兜底）

```python
@dataclass
class AlternativeSchema:
    """另类数据通用容器 --- 仅用于无具体 Schema 覆盖的子类型"""
    sub_type:  str   # "dragons" | "block_trade" | "holder_changes" | ...
    code:      str
    trade_date: date
    data:      str   # JSON string
```

#### 5.4.3 子类型路由

```python
ALTERNATIVE_SCHEMA_MAP = {
    "north_flow":   NorthFlowSchema,
    "margin_trade": MarginTradeSchema,
    # "dragons":    AlternativeSchema,  # 兜底
    # "block_trade": AlternativeSchema,
}
```

新加另类子类型时：字段固定 -> 加具体 Schema + 注册；字段灵活 -> 走 `AlternativeSchema` 通用容器。

### 5.5 ReferenceSchema（品种参考信息）

```python
@dataclass
class ReferenceSchema:
    code:       str
    name:       str               # "平安银行"
    industry:   str               # "银行"（申万一级）
    list_date:  date
    delist_date: date | None
```

### 5.6 Parquet 分区策略

| Schema | 分区键 | 路径示例 |
|--------|--------|----------|
| StockDailySchema | `asset_type` / `year` / `month` | `parquet/stock/daily/2025/01/` |
| StockMinuteSchema | `asset_type` / `frequency` / `year` / `month` | `parquet/stock/5min/2025/01/` |
| FinanceSchema | `asset_type` / `report_period` | `parquet/stock/finance/2025Q4/` |
| NorthFlowSchema | `year` / `month` | `parquet/north_flow/2025/01/` |
| MarginTradeSchema | `year` / `month` | `parquet/margin_trade/2025/01/` |
| AlternativeSchema | `sub_type` / `year` / `month` | `parquet/alt_dragons/2025/01/` (兜底) |
| ReferenceSchema | 无分区（单文件） | `parquet/_reference/` |

### 5.7 Schema 注册表 (schemas/__init__.py)

CLI 和配置通过字符串名查找 Schema 类，需要在 `schemas/` 中维护唯一映射：

```python
SCHEMA_REGISTRY: dict[str, type] = {
    "daily":        StockDailySchema,
    "minute":       StockMinuteSchema,
    "finance":      FinanceSchema,
    "alternative":  AlternativeSchema,    # 通用容器
    "north_flow":   NorthFlowSchema,       # 北向资金（另有具体 Schema）
    "margin_trade": MarginTradeSchema,     # 融资融券（另有具体 Schema）
    "reference":    ReferenceSchema,
}
```

同时 `source_priority.yaml` 的顶层 key（`daily` / `minute` / `finance` / `alternative`）与 `SCHEMA_REGISTRY` 的 key 完全一致，`SourceRegistry` 通过同一个 key 从 YAML 中读取对应 section 的优先级列表。

### 5.8 Schema 边界校验

每个 Schema 提供 `validate(df) -> list[str]` 和 `partition_values(df) -> dict` 两个类方法，在 `SourceNode.fetch()` 返回后立即调用，**在数据源边界发现字段问题**，避免错误传播到清洗/存储层后难以定位根因：

```python
@dataclass
class StockDailySchema:
    ...  # fields

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验必需列、类型、非负约束。返回空列表 = 通过"""
        issues = []
        required = {"code", "trade_date", "open", "high", "low", "close", "volume", "amount"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
        if (df["high"] < df["low"]).any():
            issues.append("high < low detected")
        if (df[["open", "high", "low", "close"]] < 0).any().any():
            issues.append("Negative price detected")
        if (df["volume"] < 0).any():
            issues.append("Negative volume detected")
        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """从数据列提取分区键值"""
        return {
            "asset_type": df["asset_type"].iloc[0],
            "year": str(df["trade_date"].dt.year.iloc[0]),
            "month": str(df["trade_date"].dt.month.iloc[0]).zfill(2),
        }
```

校验失败 -> pipeline 记录 warning 日志，过滤脏行后继续，问题写入 `PipelineReport.issues`。

---

## 6. 数据源插件规范

每个数据源子包结构相同：

```
sources/<name>/
├── __init__.py      # 导出 SourceNode 子类
├── client.py        # API 调用封装（请求/重试/限速/序列化）
├── downloader.py    # 实现 SourceNode（调 client + 调 mapper）
└── mapper.py        # 原始字段 -> 内部 Schema 字段（列重命名/单位转换/类型转换）
```

### 6.1 插件注册 (sources/registry.py)

```python
class SourceRegistry:
    """
    按 Schema 类型维护独立的优先级降级链。
    source_priority.yaml 中每个 section（daily/minute/finance/alternative）
    对应一条降级链，初始化时通过 SCHEMA_REGISTRY 将 section key 映射到 Schema 类。
    """

    def __init__(self, config: dict):
        # _priorities: {Schema类: [(source_name, priority), ...], ...}
        self._priorities: dict[type, list[tuple[str, int]]] = {}
        self._sources: dict[str, SourceNode] = {}

    def register(self, source: SourceNode, priority: int, schema: type):
        """为指定 Schema 类型注册数据源及优先级"""
        self._sources[source.name] = source
        if schema not in self._priorities:
            self._priorities[schema] = []
        self._priorities[schema].append((source.name, priority))
        self._priorities[schema].sort(key=lambda x: x[1], reverse=True)

    @property
    def primary(self) -> str | None:
        """全局最高优先级数据源（跨所有 Schema 类型）"""
        # 取第一个注册的源中优先级最高的
        for priorities in self._priorities.values():
            if priorities:
                return priorities[0][0]
        return None

    def get_all(self, asset_type: str, schema: type) -> list[SourceNode]:
        """按优先级降序返回支持该品种+数据模型的所有源"""
        candidates = self._priorities.get(schema, [])
        return [
            self._sources[name]
            for name, _ in candidates
            if name in self._sources and self._sources[name].supports(asset_type, schema)
        ]
```

初始化时遍历 `source_priority.yaml` 各 section，通过 `SCHEMA_REGISTRY[section_key]` 得到 Schema 类，再逐条调用 `register(source, priority, schema)`。

### 6.2 mapper 规范

每个 mapper 实现两个方法：

```python
# sources/akstock/mapper.py
def to_internal(df: pd.DataFrame) -> pd.DataFrame:
    """akshare 原始字段 -> 内部标准字段"""
    return df.rename(columns={
        "日期": "trade_date",
        "开盘": "open",
        "收盘": "close",
        # ... 列重命名 + 类型转换 + 单位适配
    })[STANDARD_COLUMNS]  # 只保留 schema 定义的列（常量由 schemas 模块导出）

def to_internal_code(raw_code: str) -> str:
    """统一代码格式: '000001' -> '000001.SZ'"""
    ...
```

`STANDARD_COLUMNS` 由各 Schema 在 `schemas/` 中定义为模块级常量，mapper 直接引用。

---

## 7. 可观测性设计

### 7.1 结构化日志 (observability/logger.py)

```python
# 每条日志包含: task_id, timestamp, level, step, message, extra
# 输出到 logs/YYYY-MM-DD/task_{task_id}.jsonl

class PipelineLogger:
    def __init__(self, log_dir: str = "logs", retention_days: int = 90):
        ...

    def log(self, level: str, step: str, message: str, **extra):
        """写入一条结构化日志"""
        ...

    def cleanup(self):
        """删除 retention_days 天之前的日志目录，防止磁盘堆积"""
        ...
```

日志保留 90 天，超过自动清理。`pipeline.yaml` 中可配置：

```yaml
logging:
  dir: "logs"
  retention_days: 90
```
```

### 7.2 任务元数据 (observability/tracer.py)

```python
# SQLite 存储每次 Pipeline 运行的元数据
# 表: task_runs
#   id TEXT PRIMARY KEY       (UUID)
#   started_at TEXT
#   finished_at TEXT
#   source_name TEXT
#   spec_json TEXT            (FetchSpec 序列化)
#   status TEXT               (success/partial/failed)
#   records_fetched INTEGER
#   records_after_clean INTEGER
#   records_written INTEGER
#   duration_ms INTEGER
#   issues_json TEXT
#   fallback_used TEXT
#   failed_codes_json TEXT
#
# 表: data_snapshots
#   date TEXT
#   schema_name TEXT
#   partition_key TEXT
#   record_count INTEGER
#   source_name TEXT
#   checksum TEXT
```

---

## 8. 配置文件规格

### 8.1 instruments.yaml

```yaml
stocks:
  market: ["sh", "sz", "bj"]      # 沪/深/京
  status: ["listed"]              # 仅上市状态（不含退市）

indices:
  codes: ["000001", "000300", "000905", "399001", ...]

etf:
  min_days: 120                   # 上市不足120天的不纳入

convertible_bonds:
  include_delisted: false

futures:
  exchanges: ["CFFEX", "SHFE", "DCE", "CZCE"]

options:
  exchanges: ["SSE", "SZSE"]
```

### 8.2 source_priority.yaml

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
      token: ${TUSHARE_TOKEN}    # 从环境变量读取

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

alternative:
  - name: akstock
    priority: 100
  - name: tushare
    priority: 50

north_flow:
  - name: akstock
    priority: 100
  - name: tushare
    priority: 50

margin_trade:
  - name: akstock
    priority: 100
  - name: tushare
    priority: 50
```

顶层 key 与 `SCHEMA_REGISTRY` 的 key 一一对应。新增具体另类 Schema 时同步在此追加 section。

### 8.3 pipeline.yaml

```yaml
data_dir: "data"
log_dir: "logs"

retry:
  max_attempts: 3
  base_delay_s: 5.0
  backoff_multiplier: 2

timeout:
  source_request_s: 60
  pipeline_run_s: 600

cleaner:
  profile: "baseline"            # "baseline" | "advanced"

storage:
  backend: "parquet"
  compression: "zstd"
  compression_level: 3

logging:
  dir: "logs"
  retention_days: 90
```

---

## 9. CLI 入口设计

```python
# cli.py --- 基于 click

@click.group()
def cli():
    pass

@cli.command()
@click.option("--asset-type", required=True)
@click.option("--schema", required=True, help="daily|minute|finance|alternative")
@click.option("--codes", default=None, help="逗号分隔，默认全部")
@click.option("--start-date", required=True)
@click.option("--end-date", default=None, help="默认今天")
@click.option("--frequency", default="daily")
def fetch(asset_type, schema, codes, start_date, end_date, frequency):
    """下载数据 -> 清洗 -> 存储，单次运行"""
    ...

@cli.command()
@click.option("--asset-type", required=True)
@click.option("--schema", required=True)
def update(asset_type, schema):
    """
    日更新：
    1. 通过 StorageBackend.read() 查询已有数据的最新 trade_date
    2. 以 latest_date + 1 天作为 start_date，today 作为 end_date
    3. 构建 FetchSpec -> PipelineRunner.run() 增量下载
    4. StorageBackend.upsert() 按 (code, trade_date) 去重写入
    5. 若无已有数据（首次运行），自动退回全量下载模式
    """
    ...

@cli.command()
def status():
    """查看最近任务运行状态（查询 SQLite 元数据表）"""
    ...
```

示例用法:
```bash
# 一次性回填 10 年历史日线
python -m aistock.cli fetch --asset-type stock --schema daily --start-date 2015-01-01

# 每日更新
python -m aistock.cli update --asset-type stock --schema daily
```

### 9.1 组合根 (bootstrap)

CLI 命令执行前的初始化逻辑，组装所有依赖并注入 `PipelineRunner`：

```python
# cli.py --- bootstrap 逻辑（每个命令调用前执行）

import uuid, yaml
from aistock.schemas import SCHEMA_REGISTRY
from aistock.sources.registry import SourceRegistry
from aistock.pipeline.cleaner import Cleaner, STEPS_BASELINE, STEPS_ADVANCED
from aistock.storage.router import get_backend
from aistock.observability.logger import PipelineLogger
from aistock.pipeline.runner import PipelineRunner
from aistock.pipeline.models import FetchSpec, PipelineContext

def _build_runner() -> PipelineRunner:
    """组合根：加载配置 -> 组装组件 -> 注入 Runner"""
    # 1. 加载配置
    with open("config/pipeline.yaml") as f:
        config = yaml.safe_load(f)
    with open("config/source_priority.yaml") as f:
        source_cfg = yaml.safe_load(f)

    # 2. 初始化 Logger
    logger = PipelineLogger(log_dir=config["log_dir"])

    # 3. 构建 SourceRegistry（按 Schema 类型注册优先级）
    registry = SourceRegistry(source_cfg)
    for section_key, entries in source_cfg.items():
        schema_cls = SCHEMA_REGISTRY[section_key]
        for entry in entries:
            source = _instantiate_source(entry["name"], entry.get("config", {}))
            registry.register(source, entry["priority"], schema_cls)

    # 4. 选择清洗链
    profile = config["cleaner"]["profile"]
    steps = STEPS_BASELINE if profile == "baseline" else STEPS_ADVANCED
    cleaner = Cleaner(steps)

    # 5. 获取存储后端
    store = get_backend(config)

    # 6. 创建上下文
    ctx = PipelineContext(
        task_id=str(uuid.uuid4()),
        config=config,
        log=logger,
    )

    return PipelineRunner(registry, cleaner, store, ctx)
```

---

## 10. 依赖 (pyproject.toml 核心依赖)

```toml
[project]
name = "aistock"
requires-python = ">=3.13"
dependencies = [
    "akshare>=1.16",
    "baostock",
    "tushare",
    "pandas>=2.2",
    "pyarrow>=18",        # Parquet 读写
    "click>=8",            # CLI
    "pyyaml>=6",           # 配置解析
    # Phase 2 预留（不安装在 Phase 1）:
    # "sqlalchemy>=2",
    # "asyncpg>=0.30",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "ruff>=0.8",
    "jupyter",
    "ipykernel",
]
```

---

## 11. 验证与测试

测试先于实现。每个组件必须有对应的验证脚本，每个实施步骤必须有明确的验收标准。

### 11.1 测试分层

```
tests/
├── unit/                              # 单元测试（无外部依赖）
│   ├── test_schemas.py                #   Schema 字段定义 & validate()
│   ├── test_cleaning_steps.py         #   每个 CleaningStep 独立测试
│   ├── test_source_registry.py        #   注册/优先级/查询
│   ├── test_exceptions.py            #   异常继承链
│   ├── test_query_spec.py            #   QuerySpec 字段组合
│   └── test_partition.py             #   分区键推导
│
├── integration/                       # 集成测试（含真实 IO）
│   ├── test_parquet_backend.py        #   write/read/upsert/exists 往返
│   ├── test_pipeline_runner.py        #   全链路（mock source + 真实 cleaner + 真实 store）
│   ├── test_fallback_chain.py         #   降级链（mock 多源依次失败）
│   ├── test_observability.py          #   日志写入 + SQLite 查询
│   └── test_cli.py                    #   CLI 命令端到端
│
├── fixtures/                          # 测试固件
│   ├── sample_daily_good.parquet      #   合法日线数据（10只×5天）
│   ├── sample_daily_bad.csv           #   含脏数据的日线（用于清洗测试）
│   ├── sample_finance.csv             #   合法财务数据
│   └── mock_responses/                #   API mock 的 JSON 响应
│       ├── akstock_daily.json
│       ├── baostock_daily.json
│       └── tushare_daily.json
│
└── conftest.py                        # 共享 fixture（如 mock PipelineContext）
```

### 11.2 组件级验证规格

#### schemas/

| 测试类 | 验证点 | 文件 |
|--------|--------|------|
| 字段定义 | 所有 Schema 类可实例化，字段类型正确 | `test_schemas.py` |
| `validate()` | 合法数据通过；缺列/高低倒挂/负价格/负成交量各自检出 | `test_schemas.py` |
| `partition_values()` | 输入 DF 返回正确的分区 dict | `test_schemas.py` |
| `SCHEMA_REGISTRY` | 所有 key 映射到正确的类 | `test_schemas.py` |

```python
# tests/unit/test_schemas.py 示例

class TestStockDailySchema:
    def test_validate_passes_on_clean_data(self, df_daily_good):
        assert StockDailySchema.validate(df_daily_good) == []

    def test_validate_detects_missing_columns(self, df_daily_good):
        df = df_daily_good.drop(columns=["volume"])
        issues = StockDailySchema.validate(df)
        assert any("volume" in i.lower() for i in issues)

    def test_validate_detects_high_low_inversion(self, df_daily_good):
        df = df_daily_good.copy()
        df.loc[0, "high"] = df.loc[0, "low"] - 1.0
        issues = StockDailySchema.validate(df)
        assert any("high" in i.lower() and "low" in i.lower() for i in issues)

    def test_partition_values_returns_correct_dict(self, df_daily_good):
        pv = StockDailySchema.partition_values(df_daily_good)
        assert pv["asset_type"] == "stock"
        assert pv["year"] == "2025"
        assert pv["month"] == "01"
```

#### pipeline/

| 测试类 | 验证点 | 文件 |
|--------|--------|------|
| 模型实例化 | FetchSpec/PipelineContext/PipelineReport/WriteResult 构造 | `test_schemas.py` |
| SourceNode | 抽象类无法直接实例化 | `test_source_registry.py` |
| SourceRegistry | register 后 get_all 返回正确顺序 | `test_source_registry.py` |
| SourceRegistry | 不同 Schema 类型有独立优先级 | `test_source_registry.py` |
| Cleaner | 按 STEPS_BASELINE 顺序执行，issues 汇总 | `test_cleaning_steps.py` |
| PipelineRunner | 成功路径返回 PipelineReport(status="success") | `test_pipeline_runner.py` |
| PipelineRunner | 第一源失败→降级→第二源成功 | `test_fallback_chain.py` |
| PipelineRunner | 所有源失败→raise PipelineError | `test_fallback_chain.py` |

```python
# tests/unit/test_source_registry.py 示例

class TestSourceRegistry:
    def test_get_all_respects_priority_order(self):
        registry = SourceRegistry({})
        ak = FakeAkSource()
        bs = FakeBsSource()
        registry.register(ak, priority=100, schema=StockDailySchema)
        registry.register(bs, priority=50, schema=StockDailySchema)
        sources = registry.get_all("stock", StockDailySchema)
        assert [s.name for s in sources] == ["akstock", "baostock"]

    def test_different_schemas_have_independent_priorities(self):
        registry = SourceRegistry({})
        ak = FakeAkSource()
        bs = FakeBsSource()
        registry.register(ak, priority=100, schema=StockDailySchema)
        registry.register(bs, priority=50, schema=StockMinuteSchema)
        # daily: ak only, minute: bs only
        assert len(registry.get_all("stock", StockDailySchema)) == 1
        assert len(registry.get_all("stock", StockMinuteSchema)) == 1
```

#### storage/parquet/

| 测试类 | 验证点 | 文件 |
|--------|--------|------|
| write + read 往返 | 写入→读取 数据一致 | `test_parquet_backend.py` |
| upsert | 新数据覆盖同主键旧行，追加新行 | `test_parquet_backend.py` |
| exists | 检查分区是否存在 | `test_parquet_backend.py` |
| 分区路径 | 分区键正确映射到目录路径 | `test_partition.py` |

```python
# tests/integration/test_parquet_backend.py 示例

class TestParquetBackend:
    def test_write_and_read_roundtrip(self, backend, df_daily_good, tmp_path):
        pkeys = StockDailySchema.partition_values(df_daily_good)
        backend.write(df_daily_good, StockDailySchema, pkeys)
        query = QuerySpec(schema=StockDailySchema, partition_keys=pkeys)
        result = backend.read(query)
        pd.testing.assert_frame_equal(result, df_daily_good, check_dtype=False)

    def test_upsert_overwrites_existing_keys(self, backend, df_daily_good):
        pkeys = StockDailySchema.partition_values(df_daily_good)
        backend.write(df_daily_good, StockDailySchema, pkeys)
        # 修改 close 价格后 upsert
        df_updated = df_daily_good.copy()
        df_updated.loc[0, "close"] = 999.99
        backend.upsert(df_updated, StockDailySchema, pkeys,
                       on_conflict=["code", "trade_date"])
        result = backend.read(QuerySpec(schema=StockDailySchema, partition_keys=pkeys))
        assert result.loc[0, "close"] == 999.99

    def test_exists_for_written_partition(self, backend, df_daily_good):
        pkeys = StockDailySchema.partition_values(df_daily_good)
        assert not backend.exists(StockDailySchema, pkeys)
        backend.write(df_daily_good, StockDailySchema, pkeys)
        assert backend.exists(StockDailySchema, pkeys)
```

#### cleaning/

| 测试类 | 验证点 | 文件 |
|--------|--------|------|
| UniversalCleaner | 完全重复行→移除；null 值处理 | `test_cleaning_steps.py` |
| UniversalCleaner | 代码格式 `000001`→`000001.SZ` | `test_cleaning_steps.py` |
| AdjustmentCleaner | 复权因子列转换为前复权价格 | `test_cleaning_steps.py` |
| StatusCleaner | ST/停牌标记正确设置 | `test_cleaning_steps.py` |
| OHLCValidator | 高低倒挂检出；量价非负校验 | `test_cleaning_steps.py` |
| Cleaner 编排 | 步骤顺序执行；某步抛 CleanError→终止 | `test_cleaning_steps.py` |

```python
# tests/unit/test_cleaning_steps.py 示例

class TestOHLCValidator:
    def test_passes_on_valid_data(self, df_daily_good):
        step = OHLCValidator()
        result = step.clean(df_daily_good, mock_context())
        assert len(result) == len(df_daily_good)

    def test_raises_on_severe_data(self):
        step = OHLCValidator()
        df = pd.DataFrame({
            "code": ["000001.SZ"],
            "trade_date": [date.today()],
            "open": [-10.0], "high": [5.0], "low": [6.0],  # open负值 + high<low
            "close": [5.0], "volume": [1000], "amount": [5000.0],
        })
        issues = step.validate(df)
        assert len(issues) >= 2
```

#### sources/

| 测试类 | 验证点 | 文件 |
|--------|--------|------|
| mapper | 中文列名→内部列名映射正确 | `test_cleaning_steps.py` |
| mapper | 代码格式统一：去除后缀、补齐前导零 | `test_cleaning_steps.py` |
| client | 真实 API 连通性（标记为 slow，CI 跳过） | `test_pipeline_runner.py` |
| downloader | 返回的 DF 列与 Schema 一致 | `test_pipeline_runner.py` |
| 降级 | mock 第一源抛异常→Runner 自动切第二源 | `test_fallback_chain.py` |

```python
# tests/integration/test_fallback_chain.py 示例

class TestFallbackChain:
    def test_second_source_used_when_first_unavailable(self, tmp_path):
        """akstock 不可达→baostock 成功"""
        ak = FailingSource("akstock", raises=SourceUnavailable())
        bs = StubSource("baostock", returns=df_daily_good())
        registry = SourceRegistry({})
        registry.register(ak, priority=100, schema=StockDailySchema)
        registry.register(bs, priority=80, schema=StockDailySchema)
        runner = build_runner(registry, tmp_path)
        report = runner.run(FetchSpec(
            asset_type="stock", codes=["000001.SZ"],
            start_date=date(2025,1,2), end_date=date(2025,1,6),
            schema=StockDailySchema
        ))
        assert report.status == "success"
        assert report.fallback_used == "baostock"
        assert report.source_name == "baostock"

    def test_all_exhausted_raises_error(self, tmp_path):
        """三个源全部失败"""
        sources = [FailingSource(f"s{i}", raises=SourceUnavailable()) for i in range(3)]
        registry = SourceRegistry({})
        for s in sources:
            registry.register(s, priority=100, schema=StockDailySchema)
        runner = build_runner(registry, tmp_path)
        with pytest.raises(PipelineError, match="All sources exhausted"):
            runner.run(FetchSpec(
                asset_type="stock", codes=["000001.SZ"],
                start_date=date(2025,1,2), end_date=date(2025,1,6),
                schema=StockDailySchema
            ))
```

#### observability/

| 测试类 | 验证点 | 文件 |
|--------|--------|------|
| logger | JSONL 格式正确，包含 task_id/timestamp/step | `test_observability.py` |
| logger | 日志文件路径按天分区 | `test_observability.py` |
| tracer | task_runs 表写入成功，字段完整 | `test_observability.py` |
| tracer | data_snapshots 写入 + 查询一致 | `test_observability.py` |

#### CLI

| 测试类 | 验证点 | 文件 |
|--------|--------|------|
| fetch 命令 | 参数解析正确，Runner 被调用 | `test_cli.py` |
| update 命令 | 检查已有日期→增量下载 | `test_cli.py` |
| status 命令 | 查询 SQLite 返回最近运行记录 | `test_cli.py` |

### 11.3 测试固件规格

```python
# tests/conftest.py — 共享 fixture

@pytest.fixture
def df_daily_good():
    """5只股票×5天合法日线"""
    codes = ["000001.SZ", "600000.SH", "000002.SZ", "600036.SH", "000858.SZ"]
    dates = pd.date_range("2025-01-02", "2025-01-06", freq="B")
    rows = []
    for code in codes:
        for d in dates:
            rows.append({
                "code": code,
                "trade_date": d.date(),
                "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2,
                "volume": 1000000, "amount": 10200000.0,
                "turnover": 0.02, "adj_factor": 1.0,
                "is_st": False, "is_suspended": False,
                "asset_type": "stock",
            })
    return pd.DataFrame(rows)

@pytest.fixture
def df_daily_bad():
    """含脏数据的日线：缺列、负价、倒挂、重复"""
    return pd.read_csv("tests/fixtures/sample_daily_bad.csv")

@pytest.fixture
def mock_context():
    return PipelineContext(task_id="test-001", config={}, log=logging.getLogger("test"))

@pytest.fixture
def backend(tmp_path):
    return ParquetBackend({"data_dir": str(tmp_path), "compression": "zstd"})
```

### 11.4 实施步骤→验收标准映射

| 步骤 | 内容 | 验收标准 |
|------|------|----------|
| 3 | 项目骨架 + 依赖 | `pytest tests/` 可运行（0 个测试也通过）；`ruff check` 通过 |
| 4 | `schemas/` | §11.2 schemas 部分 4 项测试全部通过 |
| 5 | `pipeline/` 框架 | §11.2 pipeline 部分 7 项测试全部通过 |
| 6 | `storage/parquet/` | §11.2 storage 部分 5 项测试全部通过（含 write→read 往返） |
| 7 | `observability/` | §11.2 observability 部分 4 项测试通过 |
| 8 | `sources/akstock/` | mapper 测试通过 + 真实 API 连通测试通过 |
| 9 | `sources/baostock/` | mapper 测试通过 + 降级链集成测试通过 |
| 10 | `sources/tushare/` | mapper 测试通过 |
| 11 | `cleaning/` | §11.2 cleaning 部分 6 项测试全部通过 |
| 12 | `cli.py` | §11.2 CLI 部分 3 项测试通过 + 全链路集成测试通过 |
| 13 | 历史回填 | 10 年日线 parquet 可被 `StorageBackend.read()` 读取且无 schema 错误 |
| 14 | 日更新验证 | `update` 连续运行 2 天，第二天零重复记录 |

---

## 12. 实施顺序

| 步骤 | 内容 | 产出 |
|------|------|------|
| 1 | 信息采集：三大数据源能力调研 | `artifacts/research/data-source-research.md` |
| 2 | 信息采集：金融数据行业标准调研 | `artifacts/research/industry-data-standards.md` |
| 3 | 技术准备：搭建项目骨架 + 依赖安装 | 目录结构 + `pyproject.toml` |
| 4 | 实现 `schemas/` | 5 个 Schema 类 + SCHEMA_REGISTRY |
| 5 | 实现 `pipeline/` 框架 | 接口 + 模型 + Runner + 异常 |
| 6 | 实现 `storage/parquet/` | ParquetBackend + 分区策略 |
| 7 | 实现 `observability/` | JSON 日志 + SQLite 元数据 |
| 8 | 实现 `sources/akstock/` | AkShare 插件（日线 -> 清洗 -> 存储验证） |
| 9 | 实现 `sources/baostock/` | Baostock 插件 + 降级链验证 |
| 10 | 实现 `sources/tushare/` | Tushare 插件 |
| 11 | 实现 `cleaning/` | 4 个 B 级清洗步骤 |
| 12 | 实现 `cli.py` | CLI 入口 + 全链路集成测试 |
| 13 | 10 年历史数据回填 | 全品种日线数据入库 |
| 14 | 日更新流程验证 | `update` 命令 + 数据正确性校验 |
| C 级预留 | 跨源交叉验证 + 质量评分 | Phase 2 |
| 因子预留 | `factors/` 模块详细设计 | 后续阶段 |
