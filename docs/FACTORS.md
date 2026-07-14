# 因子计算层功能说明

## 概述

Aistock 因子计算层提供可扩展的因子计算框架，支持技术因子、基本面因子和另类因子的计算、存储、查询和分析。

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    因子计算框架架构                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              因子注册表 (Factor Registry)            │   │
│  │  - 因子名称、描述、版本                              │   │
│  │  - 依赖关系管理                                      │   │
│  │  - 元数据存储                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              因子计算引擎 (Factor Engine)            │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │ 技术因子 │  │ 基本面  │  │ 另类因子 │             │   │
│  │  │  动量    │  │  价值   │  │  资金流  │             │   │
│  │  │  波动率  │  │  质量   │  │  市场情绪 │             │   │
│  │  │  流动性  │  │  成长   │  │          │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              因子存储层 (Factor Storage)             │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │ Parquet │  │  缓存   │  │  查询   │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              因子分析层 (Factor Analysis)            │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │ 分析器  │  │ 标准化  │  │  缓存   │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. FactorCalculator 接口

```python
class FactorCalculator(ABC):
    """因子计算抽象接口"""
    
    @property
    @abstractmethod
    def metadata(self) -> FactorMetadata:
        """获取因子元数据"""
        ...
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算因子值"""
        ...
```

### 2. FactorRegistry 因子注册表

```python
class FactorRegistry:
    """因子注册表"""
    
    def register(self, name: str, calculator: FactorCalculator) -> None:
        """注册因子"""
        ...
    
    def get(self, name: str) -> FactorCalculator:
        """获取因子计算器"""
        ...
    
    def list_factors(self, category: FactorCategory | None = None) -> list[str]:
        """列出所有因子"""
        ...
```

### 3. FactorStorage 因子存储

```python
class FactorStorage:
    """因子存储管理器"""
    
    def save(self, factor_name: str, data: pd.DataFrame, metadata: FactorMetadata) -> str:
        """保存因子数据"""
        ...
    
    def load(self, factor_name: str) -> pd.DataFrame:
        """加载因子数据"""
        ...
    
    def exists(self, factor_name: str) -> bool:
        """检查因子数据是否存在"""
        ...
```

## 已实现的因子

### 技术因子 (12 个)

| 因子 | 说明 | 参数 |
|------|------|------|
| momentum_5d | 5日动量因子 | window=5 |
| momentum_20d | 20日动量因子 | window=20 |
| momentum_60d | 60日动量因子 | window=60 |
| volatility_20d | 20日波动率 | window=20 |
| atr_14 | 平均真实波幅 | window=14 |
| realized_vol_20d | 已实现波动率 | window=20 |
| turnover_rate | 换手率因子 | - |
| amihud_20d | Amihud 流动性 | window=20 |
| volume_momentum_20d | 成交量动量 | window=20 |
| rsi_14 | 相对强弱指标 | window=14 |
| macd | MACD 指标 | fast=12, slow=26, signal=9 |
| bollinger_bands | 布林带指标 | window=20, num_std=2.0 |

### 基本面因子 (15 个)

| 因子 | 说明 | 数据需求 |
|------|------|----------|
| pe | 市盈率 | close, eps |
| pb | 市净率 | close, bps |
| ps | 市销率 | market_cap, revenue |
| dividend_yield | 股息率 | dividend, close |
| earnings_yield | 盈利收益率 | eps, close |
| roe | 净资产收益率 | net_profit, shareholders_equity |
| gross_margin | 毛利率 | revenue, cost_of_goods_sold |
| debt_to_equity | 资产负债率 | total_liabilities, shareholders_equity |
| current_ratio | 流动比率 | current_assets, current_liabilities |
| asset_turnover | 资产周转率 | revenue, total_assets |
| revenue_growth | 营收增长率 | revenue |
| net_profit_growth | 利润增长率 | net_profit |
| eps_growth | 每股收益增长率 | eps |
| book_value_growth | 净资产增长率 | shareholders_equity |
| operating_cash_flow_growth | 经营现金流增长率 | operating_cash_flow |

### 另类因子 (9 个)

| 因子 | 说明 | 数据需求 |
|------|------|----------|
| north_flow_net | 北向资金净流入 | buy_amount, sell_amount |
| north_flow_momentum_5d | 北向资金动量 | buy_amount, sell_amount |
| margin_balance_change | 融资余额变化 | margin_balance |
| margin_ratio | 融资融券比率 | margin_balance, short_balance |
| limit_up_count | 涨停板数量 | pct_change |
| limit_down_count | 跌停板数量 | pct_change |
| advance_decline_ratio | 涨跌比 | pct_change |
| market_breadth | 市场广度 | pct_change |
| volatility_index_20d | 波动率指数 | close |

## 使用示例

### 1. 计算因子

```python
from aistock.factors.technical.momentum import Momentum20DFactor

# 创建因子计算器
factor = Momentum20DFactor()

# 计算因子
result = factor.calculate(data)

# 获取结果
factor_values = result.data["momentum_20d"]
```

### 2. 注册和管理因子

```python
from aistock.factors.registry import FactorRegistry
from aistock.factors.technical.momentum import Momentum20DFactor

# 创建注册表
registry = FactorRegistry()

# 注册因子
registry.register("momentum_20d", Momentum20DFactor())

# 获取因子
factor = registry.get("momentum_20d")

# 列出所有因子
factors = registry.list_factors()
```

### 3. 存储和查询因子

```python
from aistock.factors.storage.storage import FactorStorage, FactorQuery

# 创建存储
storage = FactorStorage("data/factors")

# 保存因子
storage.save("momentum_20d", factor_data, metadata)

# 加载因子
data = storage.load("momentum_20d")

# 查询因子
query = FactorQuery(storage)
latest = query.query_latest("momentum_20d", n=5)
```

### 4. 分析因子

```python
from aistock.factors.analysis.analyzer import FactorAnalyzer

# 创建分析器
analyzer = FactorAnalyzer()

# 分析因子
result = analyzer.analyze(factor_values, forward_returns)

# 获取分析结果
print(f"IC: {result.ic_mean:.4f}")
print(f"IR: {result.ir:.4f}")
print(f"Sharpe: {result.sharpe_ratio:.4f}")
```

## 性能优化

### 缓存机制

- **内存缓存**: 最近使用的因子数据缓存在内存中
- **磁盘缓存**: 因子数据持久化到 Parquet 文件
- **缓存装饰器**: 自动缓存函数计算结果

### 计算优化

- **向量化计算**: 使用 NumPy 和 Pandas 进行向量化因子计算
- **惰性加载**: 因子计算器按需加载
- **并行计算**: 支持多因子并行计算

## 扩展指南

### 添加新因子

1. 创建因子计算器类，继承 `FactorCalculator`
2. 实现 `metadata` 属性和 `calculate` 方法
3. 注册到 `FactorRegistry`

```python
from aistock.factors.interface import FactorCalculator, FactorMetadata, FactorResult

class MyFactor(FactorCalculator):
    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="my_factor",
            description="My custom factor",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
        )
    
    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        # 实现计算逻辑
        ...
```

### 添加新标准化方法

1. 在 `FactorNormalizer` 中添加新方法
2. 实现标准化逻辑

```python
class FactorNormalizer:
    def my_normalization(self, data: pd.Series) -> pd.Series:
        """自定义标准化方法"""
        # 实现标准化逻辑
        ...
```

## 测试

```bash
# 运行所有因子测试
pytest tests/unit/factors/ -v

# 运行集成测试
pytest tests/integration/factors/ -v
```

## 参考资料

- [Microsoft Qlib](https://github.com/microsoft/qlib)
- [alphalens-reloaded](https://github.com/stefan-jansen/alphalens-reloaded)
- [MSCI FaCS](https://www.msci.com/facs)
