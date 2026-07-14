# Sprint 9: 基本面因子

**Sprint 周期**: 2027-01-21 至 2027-02-03
**状态**: ✅ 完成
**测试数量**: 18 个

---

## 目标

实现基本面因子，包括价值、质量和成长因子。

## 实现的功能

### 1. 价值因子 (5 个)

| 因子 | 说明 | 数据需求 |
|------|------|----------|
| PEFactor | 市盈率 | close, eps |
| PBFactor | 市净率 | close, bps |
| PSFactor | 市销率 | market_cap, revenue |
| DividendYieldFactor | 股息率 | dividend, close |
| EarningsYieldFactor | 盈利收益率 | eps, close |

### 2. 质量因子 (5 个)

| 因子 | 说明 | 数据需求 |
|------|------|----------|
| ROEFactor | 净资产收益率 | net_profit, shareholders_equity |
| GrossMarginFactor | 毛利率 | revenue, cost_of_goods_sold |
| DebtToEquityFactor | 资产负债率 | total_liabilities, shareholders_equity |
| CurrentRatioFactor | 流动比率 | current_assets, current_liabilities |
| AssetTurnoverFactor | 资产周转率 | revenue, total_assets |

### 3. 成长因子 (5 个)

| 因子 | 说明 | 数据需求 |
|------|------|----------|
| RevenueGrowthFactor | 营收增长率 | revenue |
| NetProfitGrowthFactor | 利润增长率 | net_profit |
| EPSGrowthFactor | 每股收益增长率 | eps |
| BookValueGrowthFactor | 净资产增长率 | shareholders_equity |
| OperatingCashFlowGrowthFactor | 经营现金流增长率 | operating_cash_flow |

## 新增文件

| 文件 | 说明 |
|------|------|
| src/aistock/factors/fundamental/__init__.py | 基本面因子模块 |
| src/aistock/factors/fundamental/value.py | 价值因子 |
| src/aistock/factors/fundamental/quality.py | 质量因子 |
| src/aistock/factors/fundamental/growth.py | 成长因子 |
| tests/unit/factors/test_fundamental.py | 基本面因子测试 (18 个) |

## 测试结果

```
18 passed in 0.19s
```

## Git 提交

```
97750cf feat: Sprint 9 - Fundamental factors implementation
```

## 遇到的问题

1. **Pandas 频率兼容性**: Pandas 3.0+ 不再支持 `freq="Q"`，需要使用 `freq="QE"`

## 经验总结

1. **数据对齐**: 基本面数据需要按报告期对齐
2. **增长率计算**: 注意处理除零和空值情况
3. **版本兼容**: 关注依赖库的版本更新
