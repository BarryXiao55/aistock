# 2026-05-24 验证策略补充

**关联文档**: `specs/data-pipeline-design.md`

## 变更摘要

`tests/` 目录原本只有空骨架，欠缺验证规格。新增完整的 §11 验证与测试章节（~300行），包含：

| 维度 | 内容 |
|------|------|
| 测试分层 | unit / integration / fixtures 三级，含 conftest.py |
| 组件验证 | schemas(4项) / pipeline(7项) / storage(5项) / cleaning(6项) / observability(4项) / sources(4项) / CLI(3项) |
| 测试代码示例 | 8 个具体测试类，覆盖正常路径 + 异常边界 |
| 测试固件 | df_daily_good / df_daily_bad / mock_context / backend + 4 个 fixture 文件 |
| 实施验收映射 | 14 个实施步骤各自的"完成"标准（如 step 6: write→read 往返测试通过） |
