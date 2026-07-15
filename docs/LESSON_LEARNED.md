# Lesson Learned - 项目审查与修复总结

**日期**: 2026-07-15
**背景**: 
1. 执行 README Quick Start 命令时发现运行时 bug
2. 全面代码审查发现 42 个潜在问题
3. 修复所有 Critical 和 High 级别问题

---

## 第一部分：Quick Start 测试发现的 Bug

### Bug 1: update 命令 KeyError: 'asset_type'

**现象**: `python -m aistock.cli update` 报错 `KeyError: 'asset_type'`

**根因**: `cli.py` 构建 `QuerySpec` 时未传入 `partition_keys`，`backend.py` 在空 partition_keys 时调用 `get_partition_path()`，该函数对 `StockDailySchema` 硬编码要求 `asset_type` 键。

**修复**:
```python
# cli.py - 修复前
query = QuerySpec(schema=schema_cls)

# cli.py - 修复后
query = QuerySpec(schema=schema_cls, partition_keys={"asset_type": asset_type})
```

**教训**: QuerySpec 构造必须考虑 Schema 的分区需求，不能假设空 partition_keys 等于"扫描全部"。

---

### Bug 2: 空 DataFrame 调用 partition_values 崩溃

**现象**: baostock 返回空数据后，`runner.py` 调用 `partition_values(df)` 时 `IndexError`

**根因**: `runner.py:65` 无条件调用 `spec.schema.partition_values(df)`，未检查 df 是否为空。

**修复**:
```python
# runner.py - 修复前
result = self._store.write(df, spec.schema, spec.schema.partition_values(df))

# runner.py - 修复后
if df.empty:
    result_records = 0
else:
    result = self._store.write(df, spec.schema, spec.schema.partition_values(df))
    result_records = result.records_written
```

**教训**: 管道中任何步骤都可能过滤掉所有数据，写入前必须检查 DataFrame 是否为空。

---

### Bug 3: backend.py 部分分区键查询失败

**现象**: 传入 `{"asset_type": "stock"}` 时，`get_partition_path()` 尝试访问不存在的 `year`/`month` 键。

**根因**: `backend.py` 将 `partition_keys` 非空等同于"精确命中"，但实际可能只传了部分键。

**修复**: 重写 `read` 方法，根据 Schema 声明的 required_keys 判断是精确命中还是目录扫描：
```python
required_keys = ["asset_type", "year", "month"]
has_all_keys = all(k in partition_keys for k in required_keys)

if has_all_keys:
    # 精确分区命中
else:
    # 从已有键构建部分路径，递归扫描
```

**教训**: 部分键查询是合理需求（如 update 命令扫描某 asset_type 下所有数据），路径构建逻辑应区分"精确命中"和"目录扫描"。

---

## 第二部分：代码审查发现并修复的问题

### Critical 级别 (3个)

#### C1: Tushare 期货硬编码 `.UNKNOWN` 交易所后缀

**文件**: `tushare_futures/downloader.py:42`

**问题**: `ts_code = f"{code}.UNKNOWN"` — Tushare API 要求有效的交易所后缀（`.CFE`, `.SHF`, `.DCE`, `.CZC`），使用 `.UNKNOWN` 导致所有期货查询失败。

**修复**: 添加 `_map_exchange()` 方法，根据合约代码前缀推断交易所：
```python
exchange_map = {
    "if": "CFE", "ic": "CFE",  # 中金所
    "cu": "SHF", "rb": "SHF",  # 上期所
    "m": "DCE", "c": "DCE",    # 大商所
    "sr": "CZC", "cf": "CZC",  # 郑商所
}
```

---

#### C2: Tushare 期权硬编码 `.UNKNOWN` 交易所后缀

**文件**: `tushare_options/downloader.py:42`

**问题**: 同 C1，所有期权查询失败。

**修复**: 根据期权代码格式推断交易所（8位数字：`10xxxxxx`→SSE，`9xxxxxxx`→SZSE）。

---

#### C3: PipelineRunner 不捕获 ValueError

**文件**: `pipeline/runner.py:101`

**问题**: 只捕获 `(SourceUnavailable, SourceRateLimited, CleanError)`，当数据源抛出 `ValueError`（如不支持的 schema）时，整个管道崩溃而非降级到下一个数据源。

**修复**:
```python
# 修复前
except (SourceUnavailable, SourceRateLimited, CleanError) as e:

# 修复后
except (SourceUnavailable, SourceRateLimited, CleanError, ValueError) as e:
```

---

### High 级别 (5个)

#### H1: 所有 Schema 的 partition_values() 未处理空 DataFrame

**文件**: `schemas/daily.py`, `minute.py`, `finance.py`, `alternative.py`, `futures.py`, `options.py`, `convertible_bond.py`

**问题**: 所有 `partition_values()` 方法直接访问 `.iloc[0]`，对空 DataFrame 抛出 `IndexError`。

**修复**: 所有 Schema 添加空 DataFrame 防护：
```python
@staticmethod
def partition_values(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"asset_type": "stock", "year": "1970", "month": "01"}
    # 正常逻辑...
```

---

#### H2: 所有 Schema 的 partition_values() 未处理字符串日期

**问题**: `df["trade_date"].iloc[0].year` 假设值是 `date` 对象，如果包含字符串会抛 `AttributeError`。

**修复**: 添加类型检查和转换：
```python
td = df["trade_date"].iloc[0]
if isinstance(td, str):
    td = pd.to_datetime(td).date()
```

---

#### H3: FuturesSchema validate() 缺少 exchange 列检查

**文件**: `schemas/futures.py:36`

**问题**: `required` 集合不包含 `"exchange"`，但 `partition_values()` 需要它，导致 validate 通过但 partition_values 崩溃。

**修复**: 将 `"exchange"` 加入 `required` 集合。

---

#### H4: CLI 日期格式无效时抛原始 ValueError

**文件**: `cli.py:126`

**问题**: `datetime.strptime()` 对无效日期格式抛出晦涩的 ValueError。

**修复**: 添加 try/except 和友好错误提示：
```python
try:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
except ValueError:
    click.echo(f"Invalid date format: '{start_date}'. Use YYYY-MM-DD.", err=True)
    sys.exit(1)
```

---

#### H5: CLI 无 asset-type 值校验

**文件**: `cli.py:114`

**问题**: `--asset-type` 接受任意字符串，无效值导致 `PipelineError("All sources exhausted")` — 错误信息误导。

**修复**: 添加值校验：
```python
valid_asset_types = {"stock", "index", "etf", "cb", "future", "option"}
if asset_type not in valid_asset_types:
    click.echo(f"Invalid asset-type: '{asset_type}'. Must be one of: ...", err=True)
    sys.exit(1)
```

---

## 第三部分：未修复但已记录的问题

以下是 Medium/Low 级别问题，已记录在代码审查报告中，留待后续版本修复：

| 级别 | 问题 | 文件 |
|------|------|------|
| Medium | cleaner 只捕获 CleanError，其他异常会传播 | `cleaner.py:23` |
| Medium | adjustment.py 除以 NaN | `adjustment.py:43` |
| Medium | futures/options/cb cleaning 除以零 | 多个 cleaning 文件 |
| Medium | Downloader 用 print 而非 logging | 所有 downloader |
| Medium | storage/router 无配置校验 | `router.py:8` |
| Medium | exists() 吞异常导致潜在数据覆盖 | `backend.py:157` |
| Medium | akstock 指数/ETF 忽略日期参数 | `akstock/client.py:60-104` |
| Medium | CLI 无 --frequency 值校验 | `cli.py:119` |
| Low | quality.py 代码重复 | `quality.py:60-101 vs 258-304` |
| Low | factors 的 `import time` 在方法内部 | 多个 factors 文件 |
| Low | 缓存使用 MD5 而非 SHA256 | `cache.py:108` |

---

## 第四部分：通用教训

### 1. 单元测试 ≠ 端到端可用

404 个单元测试全部通过，但 Quick Start 命令仍有 bug。**单元测试验证的是函数逻辑，不是用户场景**。

**建议**: 在 CI 中增加端到端测试，至少覆盖 README 中的示例命令。

### 2. 空数据是常态，不是异常

管道中多个步骤（schema 校验、清洗、OHLC 验证）都可能过滤掉所有数据。**每个操作 DataFrame 的函数都应该考虑空输入**。

**建议**: 
- 在 Schema 中添加 `required_partition_keys` 属性
- 在关键节点（校验后、清洗后、写入前）统一检查 DataFrame 是否为空

### 3. 外部 API 的隐式契约

Tushare 期货 API 要求有效的交易所后缀，但代码中硬编码了 `.UNKNOWN`。**外部 API 的参数约束应该在代码中显式处理，而非假设**。

**建议**: 为每个数据源添加集成测试，验证实际 API 调用。

### 4. 异常捕获的粒度

`runner.py` 只捕获 3 种异常，遗漏了 `ValueError`。`backend.py` 捕获所有异常包装为 `BackendUnavailable`。**两种极端都不可取**。

**建议**: 
- 明确列出可降级的异常类型
- 区分"可恢复"和"不可恢复"异常
- 记录完整的异常链，便于调试

### 5. 配置驱动 > 硬编码

交易所映射、分区键要求等信息散落在多个文件中。**应该集中管理这些配置**。

**建议**: 创建 `src/aistock/constants.py`，统一管理交易所映射、Schema 分区键要求等。

---

## 修复文件清单

### 第一轮: Quick Start 修复

| 文件 | 修改内容 |
|------|----------|
| `cli.py:228` | 传入 `partition_keys={"asset_type": asset_type}` |
| `runner.py:64-68` | 写入前检查 DataFrame 是否为空 |
| `backend.py:57-99` | 支持部分分区键扫描 |

### 第二轮: 代码审查修复

| 文件 | 修改内容 |
|------|----------|
| `tushare_futures/downloader.py` | 添加 `_map_exchange()` 交易所映射 |
| `tushare_options/downloader.py` | 添加 `_map_exchange()` SSE/SZSE 检测 |
| `pipeline/runner.py:101` | 捕获 ValueError 防止管道崩溃 |
| `schemas/daily.py` | partition_values 空 DataFrame 防护 + 字符串日期处理 |
| `schemas/minute.py` | 同上 |
| `schemas/finance.py` | 同上 |
| `schemas/alternative.py` | 同上 (3 个 Schema) |
| `schemas/futures.py` | 同上 + validate 增加 exchange 列 |
| `schemas/options.py` | 同上 |
| `schemas/convertible_bond.py` | 同上 |
| `cli.py:126` | 日期格式校验 + 友好错误提示 |
| `cli.py:114` | asset-type 值校验 |
| `tests/unit/test_futures.py` | 测试数据补充 exchange 列 |

---

## 验证结果

- **测试**: 404 个全部通过 (2.60s)
- **fetch**: 成功获取数据
- **update**: 正常运行（今日数据未发布是预期行为）
- **status**: 正常显示任务状态
- **search**: 搜索 "贵州茅台" 返回正确结果

---

## Git 提交记录

```
dbba467 fix: critical and high severity bugs from codebase audit
7676fb2 docs: add Lesson Learned from Quick Start testing
ecc850c fix: update command crashes and partial partition key support
454cd93 docs: update documentation to match v1.0.0 codebase state
```
