# 2026-05-24 数据流审查修复

**关联文档**: `specs/data-pipeline-design.md`

## 变更摘要

端到端数据流追踪发现 7 项问题，全部修复：

| # | 严重度 | 问题 | 修复 |
|---|--------|------|------|
| 1 | 致命 | `records_fetched` 在过滤/清洗**之后**取值，与 `records_after_clean` 永远相等 | 在 `fetch_with_retry` 返回后立即捕获 `records_fetched`，清洗后单独记录 `records_after_clean` |
| 2 | 致命 | `SourceRegistry` 全局优先级列表无法表达 YAML 中按 schema type 分段的不同降级链 | `register(source, priority, schema)` 按 Schema 类型维护独立优先级列 |
| 3 | 中 | `spec.codes=None`（下载全部）时 `requested=set()`，partial 永远不触发 | 区分 None/非None 两条路径；codes=None 时以是否有产出判断 failed |
| 4 | 中 | CLI 启动时的"组合根"代码缺失：配置加载、组件组装、依赖注入 | 新增 §9.1 组合根，完整定义 `_build_runner()` 引导逻辑 |
| 5 | 低 | `_filter_invalid_rows` 行为模糊 | 改名为 `_find_invalid_rows_mask`，明确为布尔 mask + 过滤丢弃 |
| 6 | 低 | `duration_ms=...` 硬编码占位 | 改为 `int((time.monotonic() - start_time) * 1000)` 实际计时 |
| 7 | 低 | `status="failed"` 路径缺失（0 条记录获取时） | 补充 `records_fetched==0` → `status="failed"` 分支 |
