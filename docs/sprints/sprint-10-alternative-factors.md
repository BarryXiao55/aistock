# Sprint 10: 另类因子和存储

**Sprint 周期**: 2027-02-04 至 2027-02-17
**状态**: ✅ 完成
**测试数量**: 25 个

---

## 目标

实现另类因子和因子存储功能。

## 实现的功能

### 1. 资金流向因子 (4 个)

| 因子 | 说明 | 数据需求 |
|------|------|----------|
| NorthFlowNetFactor | 北向资金净流入 | buy_amount, sell_amount |
| NorthFlowMomentumFactor | 北向资金动量 | buy_amount, sell_amount |
| MarginBalanceChangeFactor | 融资余额变化 | margin_balance |
| MarginRatioFactor | 融资融券比率 | margin_balance, short_balance |

### 2. 市场情绪因子 (5 个)

| 因子 | 说明 | 数据需求 |
|------|------|----------|
| LimitUpCountFactor | 涨停板数量 | pct_change |
| LimitDownCountFactor | 跌停板数量 | pct_change |
| AdvanceDeclineRatioFactor | 涨跌比 | pct_change |
| MarketBreadthFactor | 市场广度 | pct_change |
| VolatilityIndexFactor | 波动率指数 | close |

### 3. 因子存储

- **FactorStorage**: Parquet 格式存储
- **FactorQuery**: 因子数据查询
- **FactorNormalizer**: 因子标准化 (Z-Score, MinMax, Rank)

## 新增文件

| 文件 | 说明 |
|------|------|
| src/aistock/factors/alternative/__init__.py | 另类因子模块 |
| src/aistock/factors/alternative/fund_flow.py | 资金流向因子 |
| src/aistock/factors/alternative/sentiment.py | 市场情绪因子 |
| src/aistock/factors/storage/__init__.py | 存储模块 |
| src/aistock/factors/storage/storage.py | FactorStorage |
| src/aistock/factors/storage/normalizer.py | 标准化工具 |
| tests/unit/factors/test_alternative_storage.py | 另类因子和存储测试 (25 个) |

## 测试结果

```
25 passed in 0.39s
```

## Git 提交

```
da7114b feat: Sprint 10 - Alternative factors and storage
```

## 遇到的问题

1. **Parquet 写入空 struct**: FactorMetadata 的 parameters 字段为空字典时，Parquet 无法写入
2. **解决方法**: 将 parameters 转换为 JSON 字符串

## 经验总结

1. **存储格式**: Parquet 适合因子数据存储
2. **标准化**: 因子标准化有助于比较和组合
3. **缓存机制**: 内存缓存 + 磁盘缓存提高性能
