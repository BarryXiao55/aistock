# 2026-05-24 第二轮审查修复

**关联文档**: `specs/data-pipeline-design.md`

## 变更摘要

第二轮审查发现 4 项问题，全部修复：

| # | 问题 | 修复 |
|---|------|------|
| 1 | 缺少 Schema 边界校验 — 数据源 API 字段变更时错误会传播到清洗/存储层 | 新增 §5.8 `Schema.validate(df) -> list[str]`，在 `SourceNode.fetch()` 返回前调用 |
| 2 | `AlternativeSchema.data: JSON string` 破坏列式查询 — 查询"北向资金>10亿"需全表解析 | 高频子类型（north_flow, margin_trade）拆为独立具体 Schema，低频/字段不定者保留 JSON 兜底 |
| 3 | `CleanError` 不触发降级 — akstock 清洗失败时应尝试 baostock 而非直接崩溃 | `PipelineRunner` 异常捕获列表加入 `CleanError` |
| 4 | 缺失 partial success 处理 — 5000 只股票中 50 只超时就全失败 | `PipelineReport` 新增 `failed_codes` 字段，成功数据正常写入，部分失败不影响已处理数据 |
