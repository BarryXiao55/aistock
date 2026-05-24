# 2026-05-24 第三轮审查修复

**关联文档**: `specs/data-pipeline-design.md`

## 变更摘要

第三轮逐行审查发现 14 项问题，全部修复：

| # | 严重度 | 问题 | 修复 |
|---|--------|------|------|
| 1 | 致命 | 4.8 `router.py` 被插入到 §5 标题下，§5 重复出现 | 将 4.8 移到 §4.7 异常体系之后、§5 之前 |
| 2 | 致命 | `Cleaner.clean()` 签名返回 `DataFrame`，但 `PipelineRunner` 按 `tuple` 解包 | 签名改为 `-> tuple[pd.DataFrame, list[str]]` |
| 3 | 致命 | `fetch_with_retry` 中 `except SourceRateLimited:` 无 `as e`，`last_exc = e` 引用未定义变量 | 补充 `as e` |
| 4 | 致命 | `_partition_keys`、`_apply_schema_filter`、`_get_failed_codes` 三个方法只调用无定义 | 替换为内联逻辑 + `Schema.partition_values(df)` |
| 5 | 中 | `failed_codes` 由 `_get_failed_codes(spec)`（原始请求）得出，应反推实际结果 | 改为 `requested codes - df["code"]` 计算 |
| 6 | 中 | `pipeline/cleaner.py` 与 `cleaning/` 的职责分工不明确 | 补充注释：前者是编排器，后者是步骤实现 |
| 7 | 中 | `pipeline/store.py` 实际作用不明确，`PipelineRunner` 直接使用 `StorageBackend` | 从目录树中移除，存储路由由 `storage/router.py` 承担 |
| 8 | 低 | `YYY-MM-DD` 拼写错误（少一个 Y） | sed 修正 |
| 9 | 低 | 未使用 `field` 导入 | sed 移除 |
| 10 | 低 | `STOCK_DAILY_COLUMNS` 示例中未定义 | 改为 `STANDARD_COLUMNS` 并补充说明由 schemas 导出 |
| 11 | 低 | `pipeline/models.py` 示例代码存在歧义 | 移除模糊的 `...` 占位符，保持语义完整 |
| 12 | 完善 | Schema 缺少 `partition_values()` 方法 | 在 §5.8 补充 |
| 13 | 完善 | `task_runs` 表缺少 `failed_codes_json` 字段 | 补充到 §7.2 表定义 |
| 14 | 完善 | `alternative` 注册表中 `NorthFlowSchema` / `MarginTradeSchema` 的 key 在 `SCHEMA_REGISTRY` 和 `ALTERNATIVE_SCHEMA_MAP` 之间的关系 | 明确两者是不同的查找路径 |
