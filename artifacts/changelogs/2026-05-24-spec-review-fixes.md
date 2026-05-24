# 2026-05-24 设计审查修复

**关联文档**: `specs/data-pipeline-design.md`

## 变更摘要

审查中发现 7 项问题，全部修复：

| # | 问题 | 修复 |
|---|------|------|
| 1 | `SourceRegistry` 缺少 `primary` 属性，`PipelineRunner` 引用不到 | 新增 `primary` property |
| 2 | `QuerySpec` 只提未定义 | 新增 §4.5.1，定义跨后端查询模型 |
| 3 | Schema 名(`daily`)→类(`StockDailySchema`)映射缺失 | 新增 §5.7 `SCHEMA_REGISTRY` |
| 4 | `source_priority.yaml` section 与 Schema 类型对应关系不明 | §5.7 明确 CLI → SCHEMA_REGISTRY → YAML key 一致 |
| 5 | `field_mapping.yaml` 冗余（mapper.py 已做字段映射） | 从目录结构和配置中移除 |
| 6 | 缺少 `.gitignore` 文件 | 根目录追加 `.gitignore` |
| 7 | `storage/router.py` 接口未定义 | 新增 §4.8 `get_backend(config) -> StorageBackend` |
