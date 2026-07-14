# Sprint 2: 期货功能开发

## Goal
实现期货数据采集功能，包括 Schema 定义、AkShare/Tushare 数据源适配、清洗步骤和测试。

## Current Phase
Phase 1: Schema 设计

## Phases

### Phase 1: Schema 设计
- [ ] FuturesSchema 数据模型
- [ ] 更新 SCHEMA_REGISTRY
- [ ] 更新 source_priority.yaml
- **Status:** in_progress

### Phase 2: 数据源适配
- [ ] AkShare 期货 client.py
- [ ] AkShare 期货 mapper.py
- [ ] AkShare 期货 downloader.py
- [ ] Tushare 期货 client.py
- [ ] Tushare 期货 mapper.py
- [ ] Tushare 期货 downloader.py
- **Status:** pending

### Phase 3: 清洗步骤
- [ ] 期货特定清洗步骤
- [ ] 更新 STEPS_BASELINE
- **Status:** pending

### Phase 4: 测试
- [ ] 单元测试
- [ ] 集成测试
- **Status:** pending

### Phase 5: 文档与集成
- [ ] 更新功能说明文档
- [ ] 端到端测试
- **Status:** pending

## Key Decisions
- 期货 Schema 包含合约特有字段（保证金、合约乘数、交割月等）
- 优先使用 AkShare 数据源，Tushare 作为备选
- 复用现有清洗框架，添加期货特定校验

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |
