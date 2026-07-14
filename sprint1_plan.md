# Sprint 1: 可转债功能开发

## Goal
实现可转债数据采集功能，包括 Schema 定义、AkShare 数据源适配、清洗步骤和测试。

## Current Phase
Phase 1: Schema 设计

## Phases

### Phase 1: Schema 设计
- [ ] ConvertibleBondSchema 数据模型
- [ ] 更新 SCHEMA_REGISTRY
- [ ] 更新 source_priority.yaml
- **Status:** in_progress

### Phase 2: 数据源适配
- [ ] AkShare 可转债 client.py
- [ ] AkShare 可转债 mapper.py
- [ ] AkShare 可转债 downloader.py
- **Status:** pending

### Phase 3: 清洗步骤
- [ ] 可转债特定清洗步骤
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
- 可转债 Schema 包含转股相关信息（转股价格、转股比例、溢价率等）
- 优先使用 AkShare 数据源
- 复用现有清洗框架，添加可转债特定校验

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |
