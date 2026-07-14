# Phase 2 功能设计评估与开发计划

**文档版本**: 1.0
**创建日期**: 2026-07-14
**用途**: 开发评审会议

---

## 目录

1. [QualityScorer 数据质量评分](#1-qualityscorer-数据质量评分)
2. [可转债/期货/期权品种扩展](#2-可转债期货期权品种扩展)
3. [开发计划与排期](#3-开发计划与排期)
4. [资源需求与风险评估](#4-资源需求与风险评估)

---

## 1. QualityScorer 数据质量评分

### 1.1 背景与目标

**背景**: Phase 1 实现了 B 级数据清洗（去重/空值/复权/停牌标记），但缺乏量化的数据质量评估机制。QualityScorer 作为 C 级清洗步骤，为数据质量提供可量化的评分体系。

**目标**:
- 为每个数据集/分区生成质量评分 (0-100)
- 支持多维度质量评估（完整性、一致性、时效性、准确性）
- 提供质量问题的可视化报告
- 支持质量阈值告警

### 1.2 设计评估

#### 1.2.1 评分维度

| 维度 | 权重 | 评估指标 | 计算方法 |
|------|------|----------|----------|
| **完整性** | 30% | 缺失值比例 | (总字段数 - 缺失字段数) / 总字段数 |
| **一致性** | 25% | 数据冲突比例 | (总行数 - 冲突行数) / 总行数 |
| **时效性** | 20% | 数据更新延迟 | (当前日期 - 最新数据日期) / 总天数 |
| **准确性** | 25% | 校验通过比例 | 通过校验行数 / 总行数 |

#### 1.2.2 评分公式

```python
quality_score = (
    completeness_score * 0.30 +
    consistency_score * 0.25 +
    timeliness_score * 0.20 +
    accuracy_score * 0.25
)
```

#### 1.2.3 质量等级

| 等级 | 分数范围 | 说明 | 处理建议 |
|------|----------|------|----------|
| A (优秀) | 90-100 | 数据质量高 | 正常使用 |
| B (良好) | 70-89 | 轻微问题 | 记录日志 |
| C (合格) | 50-69 | 中等问题 | 告警通知 |
| D (不合格) | 0-49 | 严重问题 | 拒绝入库 |

#### 1.2.4 技术方案

**接口设计**:
```python
class QualityScorer(CleaningStep):
    """数据质量评分步骤"""
    
    name = "quality_scorer"
    
    def clean(self, df: pd.DataFrame, ctx: PipelineContext) -> pd.DataFrame:
        """计算质量评分并添加到 DataFrame"""
        ...
    
    def validate(self, df: pd.DataFrame) -> list[str]:
        """检查质量评分是否达标"""
        ...
    
    def generate_report(self, df: pd.DataFrame) -> QualityReport:
        """生成质量报告"""
        ...
```

**数据模型**:
```python
@dataclass
class QualityReport:
    """质量评分报告"""
    schema_name: str
    partition_key: str
    total_records: int
    quality_score: float
    completeness: float
    consistency: float
    timeliness: float
    accuracy: float
    issues: list[QualityIssue]
    generated_at: datetime

@dataclass
class QualityIssue:
    """质量问题"""
    dimension: str
    severity: str  # "info" | "warning" | "error"
    description: str
    affected_rows: int
    suggestion: str
```

### 1.3 优势分析

| 优势 | 说明 |
|------|------|
| 可量化 | 0-100 评分，直观易懂 |
| 多维度 | 4 个维度覆盖主要质量指标 |
| 可配置 | 权重、阈值可配置 |
| 可扩展 | 支持自定义维度和计算方法 |
| 集成性 | 作为 CleaningStep 集成到管道 |

### 1.4 劣势与风险

| 劣势 | 风险等级 | 缓解措施 |
|------|----------|----------|
| 计算开销 | 中 | 增量计算，避免全量扫描 |
| 误报率 | 中 | 可配置规则，人工审核 |
| 维护成本 | 低 | 模块化设计，易于维护 |

### 1.5 实现优先级

**优先级**: P2 (中等)

**理由**:
- Phase 1 已有基础清洗，质量评分是锦上添花
- 不影响核心数据管道功能
- 可作为独立模块逐步迭代

---

## 2. 可转债/期货/期权品种扩展

### 2.1 背景与目标

**背景**: Phase 1 实现了股票、指数、ETF 的数据采集，但 A 股市场还包含可转债、期货、期权等品种。这些品种有独特的数据结构和业务规则。

**目标**:
- 支持可转债数据采集（转股价格、转股比例等）
- 支持期货数据采集（合约信息、保证金等）
- 支持期权数据采集（行权价、到期日等）
- 保持架构一致性，易于扩展

### 2.2 设计评估

#### 2.2.1 可转债 (Convertible Bond)

**数据特点**:
- 兼具债券和股票特性
- 需要转股相关信息
- 到期赎回条款复杂

**Schema 设计**:
```python
@dataclass
class ConvertibleBondSchema:
    """可转债 Schema"""
    code: str                    # 转债代码
    bond_code: str               # 债券代码
    stock_code: str              # 正股代码
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    
    # 可转债特有字段
    conversion_price: float      # 转股价格
    conversion_ratio: float      # 转股比例
    conversion_value: float      # 转股价值
    premium_rate: float          # 溢价率
    maturity_date: date          # 到期日
    coupon_rate: float           # 票面利率
    
    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验可转债数据"""
        ...
    
    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """分区键"""
        return {"asset_type": "cb", "year": "...", "month": "..."}
```

**数据源支持**:
| 数据源 | 支持情况 | 说明 |
|--------|----------|------|
| AkShare | ✅ | `bond_cb_jsl()` 等接口 |
| Baostock | ⚠️ | 部分支持 |
| Tushare | ✅ | `bond_cb()` 接口 |

#### 2.2.2 期货 (Futures)

**数据特点**:
- 合约标准化
- 有到期日和交割月
- 需要保证金、持仓量等信息

**Schema 设计**:
```python
@dataclass
class FuturesSchema:
    """期货 Schema"""
    code: str                    # 合约代码 (如 IF2501)
    underlying: str              # 标的物 (如 IF)
    exchange: str                # 交易所 (CFFEX/SHFE/DCE/CZCE)
    trade_date: date
    
    open: float
    high: float
    low: float
    close: float
    settle: float                # 结算价
    volume: int
    open_interest: int           # 持仓量
    
    # 期货特有字段
    margin_rate: float           # 保证金比例
    contract_multiplier: int     # 合约乘数
    delivery_month: str          # 交割月
    expiry_date: date            # 到期日
    
    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验期货数据"""
        ...
    
    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """分区键"""
        return {
            "asset_type": "future",
            "exchange": "...",
            "year": "...",
            "month": "..."
        }
```

**数据源支持**:
| 数据源 | 支持情况 | 说明 |
|--------|----------|------|
| AkShare | ✅ | `futures_zh_daily_sina()` 等接口 |
| Baostock | ❌ | 不支持 |
| Tushare | ✅ | `fut_daily()` 接口 |

#### 2.2.3 期权 (Options)

**数据特点**:
- 有行权价、到期日
- 分看涨/看跌
- 需要隐含波动率等信息

**Schema 设计**:
```python
@dataclass
class OptionsSchema:
    """期权 Schema"""
    code: str                    # 期权合约代码
    underlying: str              # 标的物
    option_type: str             # "call" | "put"
    strike_price: float          # 行权价
    expiry_date: date            # 到期日
    
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    open_interest: int
    
    # 期权特有字段
    implied_volatility: float    # 隐含波动率
    delta: float                 # Delta 值
    gamma: float                 # Gamma 值
    theta: float                 # Theta 值
    vega: float                  # Vega 值
    
    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        """校验期权数据"""
        ...
    
    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        """分区键"""
        return {
            "asset_type": "option",
            "underlying": "...",
            "option_type": "...",
            "year": "...",
            "month": "..."
        }
```

**数据源支持**:
| 数据源 | 支持情况 | 说明 |
|--------|----------|------|
| AkShare | ✅ | `option_sse_daily()` 等接口 |
| Baostock | ❌ | 不支持 |
| Tushare | ✅ | `opt_daily()` 接口 |

### 2.3 架构兼容性分析

#### 2.3.1 现有架构支持

| 组件 | 兼容性 | 需要修改 |
|------|--------|----------|
| SourceNode 接口 | ✅ | 无需修改 |
| CleaningStep 接口 | ✅ | 无需修改 |
| StorageBackend 接口 | ✅ | 无需修改 |
| SourceRegistry | ✅ | 无需修改 |
| PipelineRunner | ✅ | 无需修改 |
| ParquetBackend | ✅ | 无需修改 |

#### 2.3.2 需要新增的组件

| 组件 | 说明 | 工作量 |
|------|------|--------|
| ConvertibleBondSchema | 可转债数据模型 | 小 |
| FuturesSchema | 期货数据模型 | 小 |
| OptionsSchema | 期权数据模型 | 小 |
| 各品种清洗步骤 | 可能需要特定清洗逻辑 | 中 |
| 各数据源适配 | AkShare/Baostock/Tushare 适配 | 中 |

#### 2.3.3 分区策略

| 品种 | 分区路径 | 说明 |
|------|----------|------|
| 可转债 | `cb/year/month/` | 按月分区 |
| 期货 | `future/exchange/year/month/` | 按交易所+月分区 |
| 期权 | `option/underlying/type/year/month/` | 按标的+类型+月分区 |

### 2.4 优势分析

| 优势 | 说明 |
|------|------|
| 架构一致性 | 复用现有 SourceNode、CleaningStep、StorageBackend 接口 |
| 扩展性好 | 新增品种不影响现有代码 |
| 数据源丰富 | AkShare 和 Tushare 支持大部分品种 |
| 分区合理 | 按品种、交易所、时间分区，查询高效 |

### 2.5 劣势与风险

| 劣势 | 风险等级 | 缓解措施 |
|------|----------|----------|
| 数据源复杂性 | 高 | 优先实现 AkShare，逐步适配其他源 |
| 品种差异大 | 中 | 抽象通用接口，特殊逻辑单独处理 |
| 测试覆盖难 | 中 | 使用 mock 数据，分层测试 |
| 维护成本 | 中 | 模块化设计，文档完善 |

### 2.6 实现优先级

| 品种 | 优先级 | 理由 |
|------|--------|------|
| 可转债 | P1 (高) | 市场活跃，数据源支持好 |
| 期货 | P2 (中) | 用户需求明确，但复杂度较高 |
| 期权 | P3 (低) | 数据源支持有限，可后期扩展 |

---

## 3. 开发计划与排期

### 3.1 整体规划

**Phase 2 目标**: 扩展数据品种 + 提升数据质量

**时间范围**: 2026-08-01 至 2026-09-30 (8 周)

### 3.2 详细排期

#### Sprint 1: 可转债支持 (2026-08-01 至 2026-08-14)

| 任务 | 负责人 | 工作量 | 交付物 |
|------|--------|--------|--------|
| ConvertibleBondSchema 设计 | - | 2 天 | Schema 定义 |
| AkShare 可转债数据源适配 | - | 3 天 | client.py, downloader.py, mapper.py |
| 可转债清洗步骤 | - | 2 天 | cleaning/cb.py |
| 单元测试 | - | 2 天 | test_convertible_bond.py |
| 集成测试 | - | 1 天 | 验证数据采集流程 |
| 文档更新 | - | 1 天 | 功能说明文档 |

**Sprint 1 交付物**:
- ConvertibleBondSchema
- AkShare 可转债数据源
- 可转债清洗步骤
- 测试用例

#### Sprint 2: 期货支持 (2026-08-15 至 2026-08-28)

| 任务 | 负责人 | 工作量 | 交付物 |
|------|--------|--------|--------|
| FuturesSchema 设计 | - | 2 天 | Schema 定义 |
| AkShare 期货数据源适配 | - | 3 天 | client.py, downloader.py, mapper.py |
| Tushare 期货数据源适配 | - | 3 天 | client.py, downloader.py, mapper.py |
| 期货清洗步骤 | - | 2 天 | cleaning/futures.py |
| 单元测试 | - | 2 天 | test_futures.py |
| 集成测试 | - | 1 天 | 验证数据采集流程 |

**Sprint 2 交付物**:
- FuturesSchema
- AkShare/Tushare 期货数据源
- 期货清洗步骤
- 测试用例

#### Sprint 3: 期权支持 (2026-08-29 至 2026-09-11)

| 任务 | 负责人 | 工作量 | 交付物 |
|------|--------|--------|--------|
| OptionsSchema 设计 | - | 2 天 | Schema 定义 |
| AkShare 期权数据源适配 | - | 3 天 | client.py, downloader.py, mapper.py |
| Tushare 期权数据源适配 | - | 3 天 | client.py, downloader.py, mapper.py |
| 期权清洗步骤 | - | 2 天 | cleaning/options.py |
| 单元测试 | - | 2 天 | test_options.py |
| 集成测试 | - | 1 天 | 验证数据采集流程 |

**Sprint 3 交付物**:
- OptionsSchema
- AkShare/Tushare 期权数据源
- 期权清洗步骤
- 测试用例

#### Sprint 4: QualityScorer (2026-09-12 至 2026-09-25)

| 任务 | 负责人 | 工作量 | 交付物 |
|------|--------|--------|--------|
| QualityScorer 接口设计 | - | 2 天 | 接口定义 |
| 评分算法实现 | - | 3 天 | scoring.py |
| 质量报告生成 | - | 2 天 | report.py |
| 集成到 Cleaner | - | 1 天 | 更新 cleaner.py |
| 单元测试 | - | 2 天 | test_quality_scorer.py |
| 集成测试 | - | 1 天 | 验证评分流程 |
| 文档更新 | - | 1 天 | 功能说明文档 |

**Sprint 4 交付物**:
- QualityScorer 清洗步骤
- 质量报告生成器
- 测试用例

#### Sprint 5: 集成与优化 (2026-09-26 至 2026-09-30)

| 任务 | 负责人 | 工作量 | 交付物 |
|------|--------|--------|--------|
| 端到端测试 | - | 2 天 | 全流程验证 |
| 性能优化 | - | 1 天 | 优化报告 |
| 文档完善 | - | 1 天 | 完整文档 |
| 代码审查 | - | 1 天 | 审查报告 |

**Sprint 5 交付物**:
- 完整的 Phase 2 实现
- 性能优化报告
- 完整文档

### 3.3 里程碑

| 里程碑 | 日期 | 交付物 | 验收标准 |
|--------|------|--------|----------|
| M1: 可转债支持 | 2026-08-14 | 可转债数据采集 | 可下载可转债日线数据 |
| M2: 期货支持 | 2026-08-28 | 期货数据采集 | 可下载期货日线数据 |
| M3: 期权支持 | 2026-09-11 | 期权数据采集 | 可下载期权日线数据 |
| M4: 质量评分 | 2026-09-25 | QualityScorer | 可生成质量报告 |
| M5: Phase 2 完成 | 2026-09-30 | 完整实现 | 全部测试通过 |

---

## 4. 资源需求与风险评估

### 4.1 资源需求

#### 4.1.1 人力资源

| 角色 | 人数 | 工作量 | 说明 |
|------|------|--------|------|
| 后端开发 | 2 | 100% | 数据源适配、Schema 实现 |
| 测试工程师 | 1 | 50% | 测试用例、集成测试 |
| 技术负责人 | 1 | 25% | 架构设计、代码审查 |

**总人力需求**: 2.5 人/月

#### 4.1.2 技术资源

| 资源 | 用途 | 成本 |
|------|------|------|
| 开发环境 | 本地开发测试 | 已有 |
| 测试环境 | 集成测试 | 已有 |
| 数据源 API | AkShare/Baostock/Tushare | 免费 |
| 云存储 | Parquet 文件存储 | 低 |

#### 4.1.3 预算

| 项目 | 预算 | 说明 |
|------|------|------|
| 人力成本 | 15 万 | 2.5 人/月 × 6 万/人/月 |
| 基础设施 | 0 | 使用现有资源 |
| 数据源费用 | 0 | 使用免费 API |
| **总计** | **15 万** | - |

### 4.2 风险评估

#### 4.2.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 数据源 API 变更 | 中 | 高 | 监控 API 变更，及时适配 |
| 数据格式不一致 | 中 | 中 | 统一 Mapper 层，隔离差异 |
| 性能瓶颈 | 低 | 中 | 增量处理，避免全量扫描 |
| 存储空间不足 | 低 | 低 | 压缩存储，定期清理 |

#### 4.2.2 业务风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 用户需求变更 | 中 | 中 | 敏捷开发，快速迭代 |
| 数据质量不达标 | 中 | 高 | QualityScorer 兜底 |
| 市场变化 | 低 | 低 | 模块化设计，易于调整 |

#### 4.2.3 管理风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 进度延迟 | 中 | 中 | 预留缓冲时间，关键路径监控 |
| 人员变动 | 低 | 高 | 文档完善，知识共享 |
| 需求优先级冲突 | 中 | 中 | 明确优先级，定期评审 |

### 4.3 成功标准

#### 4.3.1 功能标准

| 标准 | 验收条件 |
|------|----------|
| 可转债支持 | 可下载可转债日线数据，数据完整 |
| 期货支持 | 可下载期货日线数据，支持主要交易所 |
| 期权支持 | 可下载期权日线数据，支持看涨/看跌 |
| QualityScorer | 可生成质量报告，评分准确 |

#### 4.3.2 质量标准

| 标准 | 验收条件 |
|------|----------|
| 测试覆盖率 | ≥ 80% |
| 测试通过率 | 100% |
| 代码审查 | 无严重问题 |
| 性能指标 | 单次下载 < 60s |

#### 4.3.3 文档标准

| 标准 | 验收条件 |
|------|----------|
| 功能说明 | 完整描述新功能 |
| API 文档 | 接口定义清晰 |
| 使用示例 | 提供典型用例 |
| 部署指南 | 可独立部署 |

---

## 附录

### A. 术语表

| 术语 | 说明 |
|------|------|
| QualityScorer | 数据质量评分组件 |
| Convertible Bond (CB) | 可转换公司债券 |
| Futures | 期货合约 |
| Options | 期权合约 |
| Schema | 数据模型定义 |
| Partition | Parquet 分区 |
| Fallback | 降级策略 |

### B. 参考文档

- [Phase 1 设计文档](../artifacts/specs/data-pipeline-design.md)
- [架构决策记录](../artifacts/adr/001-plugin-pipeline-architecture.md)
- [功能说明文档](FUNCTIONALITY.md)
- [设计目标达成评估](DESIGN_REVIEW.md)

### C. 会议议程建议

1. **开场** (5 分钟)
   - 介绍文档目的
   - 回顾 Phase 1 成果

2. **QualityScorer 评审** (20 分钟)
   - 功能介绍
   - 设计方案
   - 优势与风险

3. **品种扩展评审** (20 分钟)
   - 可转债/期货/期权设计
   - 数据源支持情况
   - 实现方案

4. **开发计划评审** (15 分钟)
   - 排期确认
   - 资源需求
   - 风险评估

5. **讨论与决策** (15 分钟)
   - 开放讨论
   - 关键决策
   - 下一步行动

6. **总结** (5 分钟)
   - 会议纪要
   - 行动项分配
