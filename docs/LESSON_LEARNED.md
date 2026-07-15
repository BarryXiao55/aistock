# Lesson Learned - Quick Start 测试修复

**日期**: 2026-07-15
**背景**: 执行 README Quick Start 三个命令（fetch、update、status）时发现 2 个 bug

---

## Bug 1: update 命令 KeyError: 'asset_type'

### 现象

```bash
python -m aistock.cli update --asset-type stock --schema daily
# 报错: KeyError: 'asset_type'
```

### 根因分析

`cli.py` 中 `update` 命令构建 `QuerySpec` 时未传入 `partition_keys`：

```python
# 修复前
query = QuerySpec(schema=schema_cls)  # 缺少 partition_keys
```

`ParquetBackend.read()` 在 `partition_keys` 为空时调用 `get_partition_path()`，而 `StockDailySchema` 的分区路径需要 `asset_type` 键，导致 KeyError。

### 修复方案

在 `cli.py:228` 传入 `asset_type` 作为分区键：

```python
# 修复后
query = QuerySpec(schema=schema_cls, partition_keys={"asset_type": asset_type})
```

### 教训

1. **QuerySpec 构造时必须考虑 Schema 的分区需求**。不同 Schema 需要不同的分区键，构造 QuerySpec 时需要根据 Schema 类型传入正确的分区键。
2. **"读取全部" 和 "精确读取" 的边界需要明确**。`backend.py` 的 `read` 方法原逻辑将 `partition_keys` 非空视为"精确命中"，但实际上可能只传了部分键（如只有 `asset_type`，没有 `year/month`）。

---

## Bug 2: 空 DataFrame 调用 partition_values 崩溃

### 现象

```bash
python -m aistock.cli update --asset-type stock --schema daily
# 报错: KeyError: 'asset_type' (在 partition_values 中)
```

### 根因分析

`runner.py:65` 在写入前无条件调用 `spec.schema.partition_values(df)`：

```python
# 修复前
result = self._store.write(df, spec.schema, spec.schema.partition_values(df))
```

当 baostock 返回的数据格式不符（如今天的数据尚未发布），所有行被 schema 校验过滤后 `df` 为空，`partition_values()` 访问 `df["asset_type"].iloc[0]` 时崩溃。

### 修复方案

在 `runner.py` 中增加空 DataFrame 判断：

```python
# 修复后
if df.empty:
    result_records = 0
else:
    result = self._store.write(df, spec.schema, spec.schema.partition_values(df))
    result_records = result.records_written
```

### 教训

1. **防御性编程：写入前检查数据是否为空**。管道中任何步骤都可能过滤掉所有数据，写入操作前必须检查 DataFrame 是否为空。
2. **schema.validate() 只报告问题，不修改数据**。过滤逻辑在 runner 中执行，但过滤后没有检查结果是否为空就直接进入了写入流程。

---

## Bug 3 (潜在): backend.py 部分分区键扫描

### 现象

`backend.py` 的 `read` 方法在 `partition_keys` 非空时走"精确命中"路径，要求所有分区键都存在。当只传部分键（如 `{"asset_type": "stock"}`）时，`get_partition_path()` 尝试访问不存在的 `year`/`month` 键导致崩溃。

### 修复方案

重写 `read` 方法的分区逻辑：

```python
# 确定该 schema 需要哪些分区键
required_keys = ["asset_type", "year", "month"]  # for StockDailySchema
has_all_keys = all(k in partition_keys for k in required_keys)

if has_all_keys:
    # 精确分区命中
    file_path = get_file_path(...)
else:
    # 从已有键构建部分路径，递归扫描
    base = self._base_dir
    if "asset_type" in partition_keys:
        base = base / partition_keys["asset_type"]
    # 递归扫描 *.parquet
```

### 教训

1. **部分键查询是合理需求**。`update` 命令需要扫描某 asset_type 下的所有年月数据来找到最新日期，只传 `asset_type` 是正常场景。
2. **路径构建逻辑应区分"精确命中"和"目录扫描"**。不能简单地用 `if partition_keys` 来判断。

---

## 通用教训

### 1. 端到端测试的重要性

单元测试 404 个全部通过，但 Quick Start 的端到端命令仍有 bug。**单元测试无法替代真实 CLI 调用测试**。

建议：在 CI 中增加端到端测试，至少覆盖 README 中的 Quick Start 命令。

### 2. 分区键 Schema 耦合

`get_partition_path()` 对每个 Schema 硬编码了分区键要求，但上层代码没有对应的约束检查。**分区策略应该自描述**，让 Schema 自己声明需要哪些分区键。

建议：在 Schema 中添加 `required_partition_keys` 属性，`backend.py` 根据 Schema 声明来决定行为。

### 3. 空数据处理

管道中的多个步骤（schema 校验、清洗、OHLC 验证）都可能过滤数据，但没有统一的"空数据检查点"。**应在关键节点（校验后、清洗后、写入前）统一检查 DataFrame 是否为空**。

---

## 修复文件清单

| 文件 | 修改内容 |
|------|----------|
| `src/aistock/cli.py:228` | 传入 `partition_keys={"asset_type": asset_type}` |
| `src/aistock/pipeline/runner.py:64-68` | 写入前检查 DataFrame 是否为空 |
| `src/aistock/storage/parquet/backend.py:57-99` | 支持部分分区键扫描 |

## 验证结果

- 404 个测试全部通过
- `fetch` 命令: 成功获取数据
- `update` 命令: 正常运行（今日数据未发布是预期行为）
- `status` 命令: 正常显示任务状态
