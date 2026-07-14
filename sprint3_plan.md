# Sprint 3: 期权功能开发

## Goal
实现期权数据采集功能，包括 Schema 定义、AkShare/Tushare 数据源适配、清洗步骤和测试。

## Current Phase
Phase 1: Schema 设计

## Phases

### Phase 1: Schema 设计
- [ ] OptionsSchema 数据模型
- [ ] 更新 SCHEMA_REGISTRY
- [ ] 更新 source_priority.yaml
- **Status:** in_progress

### Phase 2: 数据源适配
- [ ] AkShare 期权 client.py
- [ ] AkShare 期权 mapper.py
- [ ] AkShare 期权 downloader.py
- [ ] Tushare 期权 client.py
- [ ] Tushare 期权 mapper.py
- [ ] Tushare 期权 downloader.py
- **Status:** pending

### Phase 3: 清洗步骤
- [ ] 期权特定清洗步骤
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
- 期权 Schema 包含希腊字母（Delta/Gamma/Theta/Vega）和隐含波动率
- 支持看涨/看跌期权
- 优先使用 AkShare 数据源，Tushare 作为备选

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |
