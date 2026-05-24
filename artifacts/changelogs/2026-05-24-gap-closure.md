# 2026-05-24 缺口闭合

**关联文档**: `specs/data-pipeline-design.md`

## 变更摘要

全量扫描发现 5 项剩余缺口，全部闭合：

| # | 问题 | 修复 |
|---|------|------|
| 1 | `source_priority.yaml` 缺少 `north_flow`/`margin_trade` section，CLI 无法路由到新注册的具体另类 Schema | 追加两个 section，各配 akstock→tushare 降级链 |
| 2 | `FinanceSchema` 缺少 `validate()`，负资产/未来报告期等异常无校验 | 补充 validate()：列检查、负值标记、report_period 格式校验 |
| 3 | `update` 命令逻辑缺细节——"最新日期"从哪查未定义 | 明确步骤：StorageBackend.read() 查最新 date→增量→upsert；首次运行自动退回全量 |
| 4 | `pipeline.yaml` 注释提"并发"但无对应设计 | 从注释中移除，并发为后期优化项 |
| 5 | 日志无留存策略，JSONL 按天分区无限堆积 | 新增 retention_days=90，cleanup() 方法，pipeline.yaml 追加 logging 节 |
