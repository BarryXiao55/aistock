# Aistock

AI-powered A-share market data pipeline.

## Features

- **Multi-source data collection**: AkShare, Baostock, Tushare
- **Automatic fallback chain**: Primary → Backup → Optional
- **B-level data cleaning**: Dedup, null handling, forward adjustment, OHLC validation
- **Parquet storage**: Columnar format with partitioning
- **Structured JSON logging**: Task-level observability
- **SQLite task metadata**: Pipeline run tracking
- **Click CLI interface**: fetch, update, status commands

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd aistock

# Install dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Fetch historical data
python -m aistock.cli fetch --asset-type stock --schema daily --codes "000001.SZ" --start-date 2025-01-01

# Daily update
python -m aistock.cli update --asset-type stock --schema daily

# View recent tasks
python -m aistock.cli status
```

## Project Structure

```
aistock/
├── src/aistock/
│   ├── __init__.py
│   ├── exceptions.py          # 9 exception classes
│   ├── cli.py                 # CLI entry point
│   ├── schemas/               # 6 data models
│   ├── pipeline/              # Pipeline framework
│   ├── sources/               # 3 data source plugins
│   ├── cleaning/              # 4 cleaning steps
│   ├── storage/               # Parquet backend
│   └── observability/         # Logging & tracing
├── tests/
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── config/                    # Configuration files
└── artifacts/                 # Design documents
```

## Configuration

### pipeline.yaml

```yaml
data_dir: "data"
log_dir: "logs"

retry:
  max_attempts: 3
  base_delay_s: 5.0

storage:
  backend: "parquet"
  compression: "zstd"

cleaner:
  profile: "baseline"
```

### source_priority.yaml

```yaml
daily:
  - name: akstock
    priority: 100
  - name: baostock
    priority: 80
  - name: tushare
    priority: 50
    config:
      token: ${TUSHARE_TOKEN}
```

## Architecture

### Pipeline Flow

```
CLI → PipelineRunner → SourceNode → Cleaner → StorageBackend
                          ↓            ↓           ↓
                     SourceRegistry  STEPS     ParquetBackend
```

### Data Flow

1. **Fetch**: Download data from API source
2. **Validate**: Schema validation, filter invalid rows
3. **Clean**: Dedup, null handling, adjustment, status marking
4. **Store**: Write to Parquet with partitioning

## Development

### Run Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit -v

# With coverage
pytest tests/ --cov=aistock
```

### Code Quality

```bash
# Linting
ruff check src/ tests/

# Formatting
ruff format src/ tests/

# Type checking
mypy src/
```

## Documentation

- [功能说明文档](docs/FUNCTIONALITY.md) - 完整的功能说明、架构设计、配置指南
- [设计目标达成评估](docs/DESIGN_REVIEW.md) - Phase 1 设计目标达成情况
- [Phase 2 设计评审](docs/PHASE2_DESIGN_REVIEW.md) - QualityScorer 和品种扩展设计
- [Phase 2 测试报告](docs/PHASE2_TEST_REPORT.md) - 测试结果分析报告
- [Phase 3 设计评审](docs/PHASE3_DESIGN_REVIEW.md) - CrossValidator、因子计算、数据源扩展
- [Phase 3 开发计划](docs/PHASE3_DEVELOPMENT_PLAN.md) - 详细开发计划和里程碑
- [设计文档](artifacts/specs/data-pipeline-design.md) - 详细的技术设计规格
- [架构决策](artifacts/adr/001-plugin-pipeline-architecture.md) - 架构决策记录

## License

MIT
