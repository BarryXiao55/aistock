# 评估报告: akstock 指数/ETF 日期参数修复 (#7)

**日期**: 2026-07-15
**问题**: `akstock/client.py` 的 `get_index_daily()` 和 `get_etf_daily()` 忽略 `start_date`/`end_date` 参数

---

## 1. 现状

| 方法 | 当前调用 | 日期参数 | 实际行为 |
|------|---------|---------|---------|
| `get_index_daily()` | `ak.stock_zh_index_daily(symbol)` | 忽略 | 下载全量历史数据 |
| `get_etf_daily()` | `ak.fund_etf_hist_sina(symbol)` | 忽略 | 下载全量历史数据 |

---

## 2. 实际 API 测试结果

### 2.1 东方财富指数 API (`stock_zh_index_daily_em`)

```python
ak.stock_zh_index_daily_em(symbol='sh000300', start_date='20250101', end_date='20250110')
```

| 返回列 | 说明 | 与现有 mapper 兼容 |
|--------|------|-------------------|
| `date` | 日期 | 需要映射为 `trade_date` |
| `open` | 开盘价 | 兼容 |
| `close` | 收盘价 | 兼容 |
| `high` | 最高价 | 兼容 |
| `low` | 最低价 | 兼容 |
| `volume` | 成交量 | 兼容 |
| `amount` | 成交额 | 兼容 |

**结论**: 返回 7 列，英文列名，与内部 schema 基本兼容，只需将 `date` → `trade_date`。

### 2.2 东方财富 ETF API (`fund_etf_hist_em`)

```python
ak.fund_etf_hist_em(symbol='510300', period='daily', start_date='20250101', end_date='20250110')
```

| 返回列 | 说明 | 与现有 mapper 兼容 |
|--------|------|-------------------|
| `日期` | 日期 | 完全兼容 `AKSTOCK_DAILY_COLUMN_MAP` |
| `开盘` | 开盘价 | 兼容 |
| `收盘` | 收盘价 | 兼容 |
| `最高` | 最高价 | 兼容 |
| `最低` | 最低价 | 兼容 |
| `成交量` | 成交量 | 兼容 |
| `成交额` | 成交额 | 兼容 |
| `振幅` | 振幅 | 兼容 |
| `涨跌幅` | 涨跌幅 | 兼容 |
| `涨跌额` | 涨跌额 | 兼容 |
| `换手率` | 换手率 | 兼容 |

**结论**: 返回 11 列，中文列名，与现有 `AKSTOCK_DAILY_COLUMN_MAP` **完全兼容**，无需修改 mapper。

---

## 3. 修复方案

### 3.1 修改 `get_index_daily()`

```python
# 修改前
df = ak.stock_zh_index_daily(symbol=f"sh{code}")

# 修改后
df = ak.stock_zh_index_daily_em(
    symbol=f"sh{code}",
    start_date=start_date.replace("-", ""),
    end_date=end_date.replace("-", ""),
)
# 需要添加列名映射: date → trade_date
```

### 3.2 修改 `get_etf_daily()`

```python
# 修改前
df = ak.fund_etf_hist_sina(symbol=f"sz{code}")

# 修改后
df = ak.fund_etf_hist_em(
    symbol=code,  # 注意: 不需要市场前缀
    period="daily",
    start_date=start_date.replace("-", ""),
    end_date=end_date.replace("-", ""),
)
# 无需修改 mapper，现有 AKSTOCK_DAILY_COLUMN_MAP 完全兼容
```

---

## 4. 影响评估

### 4.1 正面影响

| 影响 | 说明 | 量化估算 |
|------|------|---------|
| 减少带宽 | 只下载指定日期范围 | 预计减少 50-80% |
| 降低内存 | 避免加载全量历史 | 大盘指数可省数百 MB |
| 提升速度 | 服务端过滤 | 预计提速 30-50% |
| 接口一致 | `start_date`/`end_date` 真正生效 | 消除 API 契约歧义 |

### 4.2 潜在风险

| 风险 | 级别 | 说明 | 缓解 |
|------|------|------|------|
| 数据源切换 | 中 | 新浪→东方财富 | 东方财富为主流数据源，数据质量相当 |
| ETF symbol 格式 | 低 | `fund_etf_hist_em` 不需要市场前缀 | 传参时去掉 `sz`/`sh` 前缀 |
| 限频策略差异 | 低 | 东方财富可能有不同限频 | 已有重试机制 |
| 历史数据覆盖 | 低 | 两个数据源的历史深度可能不同 | 东方财富覆盖较全 |

### 4.3 不变项

| 项目 | 说明 |
|------|------|
| 下游逻辑 | runner.py 清洗/存储流程不变 |
| 错误处理 | 重试和异常捕获逻辑不变 |
| ETF mapper | `AKSTOCK_DAILY_COLUMN_MAP` 完全兼容，无需修改 |
| Index mapper | 需要新增一个简单的列名映射 (`date` → `trade_date`) |

---

## 5. 工作量估算

| 步骤 | 工作量 |
|------|--------|
| 修改 `client.py` 两个方法 | 小 |
| 添加 index 列名映射 | 小 |
| 更新测试 | 小 |
| **总计** | **约 30 分钟** |

---

## 6. 结论

| 维度 | 评估 |
|------|------|
| 技术可行性 | **完全可行** — `_em` API 原生支持日期参数 |
| 数据兼容性 | **高** — ETF 完全兼容，Index 只需微调列名 |
| 风险等级 | **低** — 数据源质量相当，已有重试机制 |
| 收益 | **明确** — 带宽/内存/速度全面改善 |
| **建议** | **推荐实施** |

---

## 7. 实施计划

1. 修改 `client.py` 的 `get_index_daily()` 和 `get_etf_daily()`
2. 为 index 添加列名映射 (`date` → `trade_date`)
3. 调整 ETF 传参格式（去掉市场前缀）
4. 运行现有测试确认无回归
5. 端到端验证: `fetch --asset-type index --schema daily --codes "000300" --start-date 2025-01-01`
