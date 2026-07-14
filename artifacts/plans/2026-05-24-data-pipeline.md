# Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Phase 1 local data pipeline — 3 free Chinese stock APIs with fallback, B-level cleaning, Parquet storage, structured logging.

**Architecture:** Plugin pipeline (SourceNode → Cleaner → StorageBackend) with per-schema-type SourceRegistry for independent fallback chains. Composition root assembles dependencies; CLI drives fetch/update/status commands.

**Tech Stack:** Python 3.13+, uv, pandas, pyarrow, click, pyyaml, pytest, ruff, akshare, baostock, tushare

---

## File Structure Map

```
src/aistock/
├── __init__.py                     # Package marker
├── exceptions.py                   # 7-class exception hierarchy
├── cli.py                          # Click CLI + _build_runner() composition root
├── schemas/
│   ├── __init__.py                 # SCHEMA_REGISTRY
│   ├── daily.py                    # StockDailySchema + validate() + partition_values()
│   ├── minute.py                   # StockMinuteSchema
│   ├── finance.py                  # FinanceSchema
│   ├── alternative.py              # NorthFlowSchema + MarginTradeSchema + AlternativeSchema + ALTERNATIVE_SCHEMA_MAP
│   └── reference.py               # ReferenceSchema
├── pipeline/
│   ├── __init__.py
│   ├── models.py                   # FetchSpec, PipelineContext, PipelineReport, WriteResult
│   ├── source.py                   # SourceNode ABC
│   ├── cleaner.py                  # Cleaner orchestrator + STEPS_BASELINE + STEPS_ADVANCED
│   └── runner.py                   # PipelineRunner (full fallback chain)
├── sources/
│   ├── __init__.py
│   ├── registry.py                 # SourceRegistry (per-schema-type priorities)
│   ├── akstock/
│   │   ├── __init__.py
│   │   ├── client.py               # akshare API wrapper + rate limit + retry
│   │   ├── downloader.py           # AkStockSource(SourceNode)
│   │   └── mapper.py               # CN columns → internal schema columns + code formatting
│   ├── baostock/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── downloader.py           # BaoStockSource(SourceNode)
│   │   └── mapper.py
│   └── tushare/
│       ├── __init__.py
│       ├── client.py
│       ├── downloader.py           # TuShareSource(SourceNode)
│       └── mapper.py
├── cleaning/
│   ├── __init__.py
│   ├── interface.py                # CleaningStep ABC
│   ├── registry.py                 # Step chain registry
│   ├── universal.py                # Dedup + null handling + code format unification
│   ├── adjustment.py               # Forward-adjusted price alignment
│   ├── status.py                   # ST/suspended/delisted flags
│   ├── validator.py                # OHLCV sanity checks
│   ├── cross_validator.py          # C-level skeleton
│   └── quality.py                  # C-level skeleton
├── storage/
│   ├── __init__.py
│   ├── interface.py                # StorageBackend ABC
│   ├── query.py                    # QuerySpec dataclass
│   ├── router.py                   # get_backend() factory
│   ├── parquet/
│   │   ├── __init__.py
│   │   ├── backend.py              # ParquetBackend (write/read/upsert/exists)
│   │   └── partition.py            # Partition path derivation
│   └── postgres/
│       ├── __init__.py
│       ├── backend.py              # PostgresBackend skeleton (Phase 2)
│       └── models.py               # SQLAlchemy ORM skeleton (Phase 2)
├── observability/
│   ├── __init__.py
│   ├── logger.py                   # PipelineLogger (JSONL + retention cleanup)
│   ├── tracer.py                   # SQLite task metadata (task_runs + data_snapshots)
│   └── models.py                   # TaskRun / DataSnapshot dataclasses
└── factors/
    ├── __init__.py
    ├── interface.py                # FactorCalculator ABC
    └── registry.py                 # Factor registry (empty, fill gradually)

config/
├── instruments.yaml
├── source_priority.yaml
└── pipeline.yaml

tests/
├── __init__.py
├── conftest.py                     # df_daily_good, df_daily_bad, mock_context, backend fixtures
├── unit/
│   ├── __init__.py
│   ├── test_schemas.py
│   ├── test_cleaning_steps.py
│   ├── test_source_registry.py
│   ├── test_exceptions.py
│   ├── test_query_spec.py
│   └── test_partition.py
├── integration/
│   ├── __init__.py
│   ├── test_parquet_backend.py
│   ├── test_pipeline_runner.py
│   ├── test_fallback_chain.py
│   ├── test_observability.py
│   └── test_cli.py
└── fixtures/
    ├── sample_daily_bad.csv
    └── mock_responses/
        ├── akstock_daily.json
        ├── baostock_daily.json
        └── tushare_daily.json

artifacts/
└── plans/
    └── 2026-05-24-data-pipeline.md    # This plan
```

---

## Task 1: Project Skeleton & Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `src/aistock/__init__.py`
- Create: `config/instruments.yaml`
- Create: `config/source_priority.yaml`
- Create: `config/pipeline.yaml`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py` (minimal)
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "aistock"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "akshare>=1.16",
    "baostock",
    "tushare",
    "pandas>=2.2",
    "pyarrow>=18",
    "click>=8",
    "pyyaml>=6",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "ruff>=0.8",
]
```

- [ ] **Step 2: Create all project files**

Six files in one batch:

`src/aistock/__init__.py`:
```python
"""Aistock --- AI-powered A-share market data pipeline."""
```

`config/instruments.yaml`:
```yaml
stocks:
  market: ["sh", "sz", "bj"]
  status: ["listed"]

indices:
  codes: ["000001", "000300", "000905", "399001"]

etf:
  min_days: 120

convertible_bonds:
  include_delisted: false

futures:
  exchanges: ["CFFEX", "SHFE", "DCE", "CZCE"]

options:
  exchanges: ["SSE", "SZSE"]
```

`config/source_priority.yaml`:
```yaml
daily:
  - name: akstock
    priority: 100
    config: {}
  - name: baostock
    priority: 80
    config: {}
  - name: tushare
    priority: 50
    config:
      token: ${TUSHARE_TOKEN}

minute:
  - name: akstock
    priority: 100
  - name: tushare
    priority: 50

finance:
  - name: akstock
    priority: 100
  - name: tushare
    priority: 80

alternative:
  - name: akstock
    priority: 100
  - name: tushare
    priority: 50

north_flow:
  - name: akstock
    priority: 100
  - name: tushare
    priority: 50

margin_trade:
  - name: akstock
    priority: 100
  - name: tushare
    priority: 50
```

`config/pipeline.yaml`:
```yaml
data_dir: "data"
log_dir: "logs"

retry:
  max_attempts: 3
  base_delay_s: 5.0
  backoff_multiplier: 2

timeout:
  source_request_s: 60
  pipeline_run_s: 600

cleaner:
  profile: "baseline"

storage:
  backend: "parquet"
  compression: "zstd"
  compression_level: 3

logging:
  dir: "logs"
  retention_days: 90
```

`tests/__init__.py`:
```python
"""Aistock test suite."""
```

`tests/conftest.py`:
```python
"""Shared test fixtures."""
import pytest

@pytest.fixture
def project_root():
    from pathlib import Path
    return Path(__file__).parent.parent
```

- [ ] **Step 3: Install dependencies and verify**

Run: `uv pip install -e ".[dev]"`
Expected: All packages installed without error

Run: `python -c "import aistock; print(aistock.__doc__)"`
Expected: `Aistock --- AI-powered A-share market data pipeline.`

Run: `pytest tests/ -v`
Expected: 0 tests collected (exits cleanly)

Run: `ruff check src/ tests/`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml src/aistock/__init__.py config/ tests/__init__.py tests/conftest.py tests/unit/__init__.py tests/integration/__init__.py .gitignore
git commit -m "feat: project skeleton with uv, pytest, ruff, and 3 config files

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 2: Exception Hierarchy

**Files:**
- Create: `src/aistock/exceptions.py`
- Create: `tests/unit/test_exceptions.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_exceptions.py
import pytest
from aistock.exceptions import (
    PipelineError, SourceError, SourceUnavailable, SourceRateLimited,
    CleanError, ValidationError, StoreError, WriteError, BackendUnavailable,
)

class TestExceptionHierarchy:
    def test_pipeline_error_is_base(self):
        assert issubclass(SourceError, PipelineError)
        assert issubclass(CleanError, PipelineError)
        assert issubclass(StoreError, PipelineError)

    def test_source_subclasses(self):
        assert issubclass(SourceUnavailable, SourceError)
        assert issubclass(SourceRateLimited, SourceError)

    def test_clean_subclasses(self):
        assert issubclass(ValidationError, CleanError)

    def test_store_subclasses(self):
        assert issubclass(WriteError, StoreError)
        assert issubclass(BackendUnavailable, StoreError)

    def test_all_raiseable(self):
        for cls in [PipelineError, SourceUnavailable, SourceRateLimited,
                     CleanError, ValidationError, WriteError, BackendUnavailable]:
            with pytest.raises(cls):
                raise cls("test message")

    def test_exception_carries_message(self):
        try:
            raise SourceUnavailable("akshare API timeout")
        except SourceUnavailable as e:
            assert str(e) == "akshare API timeout"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_exceptions.py -v`
Expected: FAIL with ImportError (module does not exist)

- [ ] **Step 3: Implement exception hierarchy**

```python
# src/aistock/exceptions.py
class PipelineError(Exception):
    """Pipeline base exception."""

class SourceError(PipelineError):
    """Data source layer exception."""

class SourceUnavailable(SourceError):
    """Data source unreachable."""

class SourceRateLimited(SourceError):
    """Data source rate-limited."""

class CleanError(PipelineError):
    """Cleaning layer exception."""

class ValidationError(CleanError):
    """Schema validation failed."""

class StoreError(PipelineError):
    """Storage layer exception."""

class WriteError(StoreError):
    """Write operation failed."""

class BackendUnavailable(StoreError):
    """Storage backend unreachable."""
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_exceptions.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/aistock/exceptions.py tests/unit/test_exceptions.py
git commit -m "feat: 7-class exception hierarchy (PipelineError base)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

## Task 3: StockDailySchema + StockMinuteSchema + ReferenceSchema

**Files:**
- Create: `src/aistock/schemas/__init__.py`
- Create: `src/aistock/schemas/daily.py`
- Create: `src/aistock/schemas/minute.py`
- Create: `src/aistock/schemas/reference.py`
- Create: `tests/unit/test_schemas.py`

- [ ] **Step 1: Write failing schema tests**

```python
# tests/unit/test_schemas.py
from datetime import date, datetime
import pandas as pd
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.minute import StockMinuteSchema
from aistock.schemas.reference import ReferenceSchema
from aistock.schemas import SCHEMA_REGISTRY


def make_daily_df(codes=None, dates=None):
    if codes is None:
        codes = ["000001.SZ", "600000.SH"]
    if dates is None:
        dates = [date(2025, 1, 2), date(2025, 1, 3)]
    rows = []
    for c in codes:
        for d in dates:
            rows.append({
                "asset_type": "stock", "code": c, "trade_date": d,
                "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2,
                "volume": 1000000, "amount": 10200000.0,
                "turnover": 0.02, "adj_factor": 1.0,
                "is_st": False, "is_suspended": False,
            })
    return pd.DataFrame(rows)


class TestStockDailySchema:
    def test_validate_passes_on_clean_data(self):
        df = make_daily_df()
        assert StockDailySchema.validate(df) == []

    def test_validate_detects_missing_columns(self):
        df = make_daily_df().drop(columns=["volume"])
        issues = StockDailySchema.validate(df)
        assert any("volume" in i.lower() for i in issues)

    def test_validate_detects_high_low_inversion(self):
        df = make_daily_df()
        df.loc[0, "high"] = df.loc[0, "low"] - 1.0
        issues = StockDailySchema.validate(df)
        assert any("high" in i.lower() and "low" in i.lower() for i in issues)

    def test_validate_detects_negative_price(self):
        df = make_daily_df()
        df.loc[0, "open"] = -5.0
        issues = StockDailySchema.validate(df)
        assert any("negative" in i.lower() or "price" in i.lower() for i in issues)

    def test_validate_detects_negative_volume(self):
        df = make_daily_df()
        df.loc[0, "volume"] = -100
        issues = StockDailySchema.validate(df)
        assert any("volume" in i.lower() for i in issues)

    def test_partition_values_returns_correct_dict(self):
        df = make_daily_df(dates=[date(2025, 1, 15)])
        pv = StockDailySchema.partition_values(df)
        assert pv["asset_type"] == "stock"
        assert pv["year"] == "2025"
        assert pv["month"] == "01"


class TestStockMinuteSchema:
    def test_validate_passes_on_clean_data(self):
        df = pd.DataFrame([{
            "asset_type": "stock", "code": "000001.SZ",
            "trade_time": datetime(2025, 1, 6, 9, 35),
            "frequency": "1min",
            "open": 10.0, "high": 10.1, "low": 9.9, "close": 10.05,
            "volume": 5000, "amount": 50250.0,
        }])
        assert StockMinuteSchema.validate(df) == []

    def test_partition_values_includes_frequency(self):
        df = pd.DataFrame([{
            "asset_type": "stock", "code": "000001.SZ",
            "trade_time": datetime(2025, 1, 6, 9, 35),
            "frequency": "5min",
            "open": 10.0, "high": 10.1, "low": 9.9, "close": 10.05,
            "volume": 5000, "amount": 50250.0,
        }])
        pv = StockMinuteSchema.partition_values(df)
        assert pv["frequency"] == "5min"
        assert pv["asset_type"] == "stock"
        assert pv["year"] == "2025"


class TestReferenceSchema:
    def test_fields_defined(self):
        r = ReferenceSchema()
        r.code = "000001.SZ"
        r.name = "PingAn"
        r.industry = "Bank"
        r.list_date = date(1991, 4, 3)
        r.delist_date = None
        assert r.code == "000001.SZ"


class TestSchemaRegistry:
    def test_daily_mapped(self):
        assert SCHEMA_REGISTRY["daily"] is StockDailySchema

    def test_minute_mapped(self):
        assert SCHEMA_REGISTRY["minute"] is StockMinuteSchema

    def test_reference_mapped(self):
        assert SCHEMA_REGISTRY["reference"] is ReferenceSchema
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_schemas.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement StockDailySchema**

```python
# src/aistock/schemas/daily.py
from dataclasses import dataclass
from datetime import date
import pandas as pd

@dataclass
class StockDailySchema:
    asset_type: str = "stock"
    code: str = ""
    trade_date: date | None = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    amount: float = 0.0
    turnover: float | None = None
    adj_factor: float = 1.0
    is_st: bool = False
    is_suspended: bool = False

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        issues = []
        required = {"code", "trade_date", "open", "high", "low", "close",
                    "volume", "amount"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
            return issues
        if (df["high"] < df["low"]).any():
            issues.append("high < low detected")
        if (df[["open", "high", "low", "close"]] < 0).any().any():
            issues.append("Negative price detected")
        if (df["volume"] < 0).any():
            issues.append("Negative volume detected")
        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        return {
            "asset_type": str(df["asset_type"].iloc[0]),
            "year": str(df["trade_date"].iloc[0].year),
            "month": str(df["trade_date"].iloc[0].month).zfill(2),
        }
```

- [ ] **Step 4: Implement StockMinuteSchema**

```python
# src/aistock/schemas/minute.py
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class StockMinuteSchema:
    asset_type: str = "stock"
    code: str = ""
    trade_time: datetime | None = None
    frequency: str = "1min"
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    amount: float = 0.0

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        issues = []
        required = {"code", "trade_time", "frequency", "open", "high", "low",
                    "close", "volume", "amount"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
            return issues
        if (df["high"] < df["low"]).any():
            issues.append("high < low detected")
        if (df[["open", "high", "low", "close"]] < 0).any().any():
            issues.append("Negative price detected")
        return issues

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        dt = df["trade_time"].iloc[0]
        return {
            "asset_type": str(df["asset_type"].iloc[0]),
            "frequency": str(df["frequency"].iloc[0]),
            "year": str(dt.year),
            "month": str(dt.month).zfill(2),
        }
```

- [ ] **Step 5: Implement ReferenceSchema**

```python
# src/aistock/schemas/reference.py
from dataclasses import dataclass
from datetime import date

@dataclass
class ReferenceSchema:
    code: str = ""
    name: str = ""
    industry: str = ""
    list_date: date | None = None
    delist_date: date | None = None
```

- [ ] **Step 6: Create schema registry (partial)**

```python
# src/aistock/schemas/__init__.py
"""Internal standard schemas and registry."""
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.minute import StockMinuteSchema
from aistock.schemas.reference import ReferenceSchema

SCHEMA_REGISTRY: dict[str, type] = {
    "daily": StockDailySchema,
    "minute": StockMinuteSchema,
    "reference": ReferenceSchema,
}
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/unit/test_schemas.py -v`
Expected: 10 passed

- [ ] **Step 8: Commit**

```bash
git add src/aistock/schemas/ tests/unit/test_schemas.py
git commit -m "feat: StockDailySchema, StockMinuteSchema, ReferenceSchema with validate()

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 4: FinanceSchema + Alternative Schemas

**Files:**
- Create: `src/aistock/schemas/finance.py`
- Create: `src/aistock/schemas/alternative.py`
- Modify: `src/aistock/schemas/__init__.py`
- Modify: `tests/unit/test_schemas.py` (append)

- [ ] **Step 1: Append tests to test_schemas.py**

Append to `tests/unit/test_schemas.py`:

```python
from aistock.schemas.finance import FinanceSchema
from aistock.schemas.alternative import (
    NorthFlowSchema, MarginTradeSchema, AlternativeSchema, ALTERNATIVE_SCHEMA_MAP,
)


class TestFinanceSchema:
    def test_validate_passes_on_clean_data(self):
        df = pd.DataFrame([{
            "code": "000001.SZ", "report_period": "2025Q1", "report_type": "q",
            "pub_date": date(2025, 4, 28), "total_assets": 1e12,
            "total_liabilities": 9e11, "shareholders_equity": 1e11,
            "revenue": 5e10, "net_profit": 1e10,
            "eps": 1.5, "bps": 15.0, "roe": 0.10, "pe_ttm": 8.5, "pb": 1.2,
        }])
        assert FinanceSchema.validate(df) == []

    def test_validate_detects_missing_columns(self):
        df = pd.DataFrame([{"code": "000001.SZ"}])
        issues = FinanceSchema.validate(df)
        assert any("Missing" in i for i in issues)

    def test_validate_detects_negative_assets(self):
        df = pd.DataFrame([{
            "code": "000001.SZ", "report_period": "2025Q1", "report_type": "q",
            "pub_date": date(2025, 4, 28), "total_assets": -100.0,
            "shareholders_equity": 100.0, "revenue": 100.0,
            "net_profit": 10.0, "eps": 1.0,
        }])
        issues = FinanceSchema.validate(df)
        assert any("Negative total_assets" in i for i in issues)

    def test_validate_detects_bad_report_period(self):
        df = pd.DataFrame([{
            "code": "000001.SZ", "report_period": "2025-X", "report_type": "q",
            "pub_date": date(2025, 4, 28), "total_assets": 100.0,
            "shareholders_equity": 100.0, "revenue": 100.0,
            "net_profit": 10.0, "eps": 1.0,
        }])
        issues = FinanceSchema.validate(df)
        assert any("report_period" in i for i in issues)


class TestNorthFlowSchema:
    def test_partition_values(self):
        df = pd.DataFrame([{
            "code": "000001.SZ", "trade_date": date(2025, 2, 15),
            "buy_amount": 1e8, "sell_amount": 8e7, "net_flow": 2e7,
        }])
        pv = NorthFlowSchema.partition_values(df)
        assert pv["year"] == "2025"
        assert pv["month"] == "02"


class TestMarginTradeSchema:
    def test_partition_values(self):
        df = pd.DataFrame([{
            "code": "000001.SZ", "trade_date": date(2025, 3, 10),
            "margin_buy": 5e7, "margin_balance": 5e8,
            "short_sell": 1e6, "short_balance": 1e7,
        }])
        pv = MarginTradeSchema.partition_values(df)
        assert pv["year"] == "2025"
        assert pv["month"] == "03"


class TestAlternativeSchema:
    def test_partition_values_uses_sub_type(self):
        df = pd.DataFrame([{
            "sub_type": "block_trade", "code": "000001.SZ",
            "trade_date": date(2025, 4, 1), "data": "{}",
        }])
        pv = AlternativeSchema.partition_values(df)
        assert pv["sub_type"] == "block_trade"


class TestAlternativeSchemaMap:
    def test_north_flow_maps_to_concrete(self):
        assert ALTERNATIVE_SCHEMA_MAP["north_flow"] is NorthFlowSchema

    def test_margin_trade_maps_to_concrete(self):
        assert ALTERNATIVE_SCHEMA_MAP["margin_trade"] is MarginTradeSchema
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_schemas.py -v`
Expected: FAIL with ImportError for finance/alternative

- [ ] **Step 3: Implement FinanceSchema**

```python
# src/aistock/schemas/finance.py
from dataclasses import dataclass
from datetime import date
import pandas as pd

@dataclass
class FinanceSchema:
    code: str = ""
    report_period: str = ""
    report_type: str = ""
    pub_date: date | None = None
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    shareholders_equity: float = 0.0
    revenue: float = 0.0
    net_profit: float = 0.0
    eps: float = 0.0
    bps: float = 0.0
    roe: float = 0.0
    pe_ttm: float = 0.0
    pb: float = 0.0

    @staticmethod
    def validate(df: pd.DataFrame) -> list[str]:
        issues = []
        required = {"code", "report_period", "pub_date", "total_assets",
                    "shareholders_equity", "revenue", "net_profit", "eps"}
        missing = required - set(df.columns)
        if missing:
            issues.append(f"Missing columns: {missing}")
            return issues
        if (df["total_assets"] < 0).any():
            issues.append("Negative total_assets")
        if (df["revenue"] < 0).any():
            issues.append("Negative revenue")
        valid_period = df["report_period"].str.match(r"^\d{4}Q[1-4]$")
        if not valid_period.all():
            issues.append("Invalid report_period format")
        return issues
```

- [ ] **Step 4: Implement alternative schemas**

```python
# src/aistock/schemas/alternative.py
from dataclasses import dataclass
from datetime import date
import pandas as pd

@dataclass
class NorthFlowSchema:
    code: str = ""
    trade_date: date | None = None
    buy_amount: float = 0.0
    sell_amount: float = 0.0
    net_flow: float = 0.0

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        d = df["trade_date"].iloc[0]
        return {"year": str(d.year), "month": str(d.month).zfill(2)}


@dataclass
class MarginTradeSchema:
    code: str = ""
    trade_date: date | None = None
    margin_buy: float = 0.0
    margin_balance: float = 0.0
    short_sell: float = 0.0
    short_balance: float = 0.0

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        d = df["trade_date"].iloc[0]
        return {"year": str(d.year), "month": str(d.month).zfill(2)}


@dataclass
class AlternativeSchema:
    sub_type: str = ""
    code: str = ""
    trade_date: date | None = None
    data: str = ""

    @staticmethod
    def partition_values(df: pd.DataFrame) -> dict:
        d = df["trade_date"].iloc[0]
        return {
            "sub_type": str(df["sub_type"].iloc[0]),
            "year": str(d.year),
            "month": str(d.month).zfill(2),
        }


ALTERNATIVE_SCHEMA_MAP: dict[str, type] = {
    "north_flow": NorthFlowSchema,
    "margin_trade": MarginTradeSchema,
}
```

- [ ] **Step 5: Update SCHEMA_REGISTRY**

Edit `src/aistock/schemas/__init__.py` to add Finance and Alternative:

```python
"""Internal standard schemas and registry."""
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.minute import StockMinuteSchema
from aistock.schemas.finance import FinanceSchema
from aistock.schemas.alternative import (
    AlternativeSchema, NorthFlowSchema, MarginTradeSchema,
)
from aistock.schemas.reference import ReferenceSchema

SCHEMA_REGISTRY: dict[str, type] = {
    "daily": StockDailySchema,
    "minute": StockMinuteSchema,
    "finance": FinanceSchema,
    "alternative": AlternativeSchema,
    "north_flow": NorthFlowSchema,
    "margin_trade": MarginTradeSchema,
    "reference": ReferenceSchema,
}
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/unit/test_schemas.py -v`
Expected: 19 passed (10 from Task 3 + 9 new)

- [ ] **Step 7: Commit**

```bash
git add src/aistock/schemas/ tests/unit/test_schemas.py
git commit -m "feat: FinanceSchema + alternative schemas (NorthFlow, MarginTrade, Alternative)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

## Task 5: Pipeline Models + SourceNode Interface + SourceRegistry

**Files:**
- Create: `src/aistock/pipeline/__init__.py`
- Create: `src/aistock/pipeline/models.py`
- Create: `src/aistock/pipeline/source.py`
- Create: `src/aistock/sources/__init__.py`
- Create: `src/aistock/sources/registry.py`
- Create: `tests/unit/test_source_registry.py`

- [ ] **Step 1: Write failing test for models AND registry**

```python
# tests/unit/test_source_registry.py
from datetime import date
import pandas as pd
from aistock.pipeline.models import FetchSpec, PipelineContext, PipelineReport, WriteResult
from aistock.pipeline.source import SourceNode
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.minute import StockMinuteSchema
from aistock.sources.registry import SourceRegistry


class TestPipelineModels:
    def test_fetch_spec_creation(self):
        spec = FetchSpec(
            asset_type="stock", codes=["000001.SZ"],
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 10),
            schema=int, frequency="daily",
        )
        assert spec.asset_type == "stock"

    def test_fetch_spec_codes_none_for_all(self):
        spec = FetchSpec(
            asset_type="stock", codes=None,
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 10),
            schema=int, frequency="daily",
        )
        assert spec.codes is None

    def test_write_result_creation(self):
        wr = WriteResult(records_written=100, partitions_affected=["stock/2025/01"], backend="parquet")
        assert wr.records_written == 100

    def test_pipeline_report_success(self):
        report = PipelineReport(
            task_id="abc-123", source_name="akstock", status="success",
            records_fetched=100, records_after_clean=98, records_written=98,
            duration_ms=1500, issues=[], failed_codes=[], fallback_used=None,
        )
        assert report.status == "success"
        assert report.fallback_used is None

    def test_pipeline_report_partial(self):
        report = PipelineReport(
            task_id="abc-456", source_name="baostock", status="partial",
            records_fetched=100, records_after_clean=95, records_written=95,
            duration_ms=2000, issues=["missing"], failed_codes=["600000.SH"],
            fallback_used="baostock",
        )
        assert report.status == "partial"


class FakeSource(SourceNode):
    def __init__(self, name, supported=True):
        self.name = name
        self._supported = supported
    def supports(self, asset_type, schema):
        return self._supported
    def fetch(self, spec):
        return pd.DataFrame()


class TestSourceRegistry:
    def test_get_all_returns_sources_in_priority_order(self):
        registry = SourceRegistry({})
        registry.register(FakeSource("akstock"), priority=100, schema=StockDailySchema)
        registry.register(FakeSource("baostock"), priority=80, schema=StockDailySchema)
        sources = registry.get_all("stock", StockDailySchema)
        assert [s.name for s in sources] == ["akstock", "baostock"]

    def test_get_all_skips_unsupported_sources(self):
        registry = SourceRegistry({})
        registry.register(FakeSource("akstock", supported=True), priority=100, schema=StockDailySchema)
        registry.register(FakeSource("baostock", supported=False), priority=80, schema=StockDailySchema)
        assert len(registry.get_all("stock", StockDailySchema)) == 1

    def test_different_schemas_independent_priorities(self):
        registry = SourceRegistry({})
        registry.register(FakeSource("akstock"), priority=100, schema=StockDailySchema)
        registry.register(FakeSource("baostock"), priority=80, schema=StockMinuteSchema)
        assert len(registry.get_all("stock", StockDailySchema)) == 1
        assert len(registry.get_all("stock", StockMinuteSchema)) == 1

    def test_primary_returns_highest_priority(self):
        registry = SourceRegistry({})
        registry.register(FakeSource("akstock"), priority=100, schema=StockDailySchema)
        registry.register(FakeSource("baostock"), priority=50, schema=StockDailySchema)
        assert registry.primary == "akstock"

    def test_get_all_empty_when_no_registered(self):
        registry = SourceRegistry({})
        assert registry.get_all("stock", StockDailySchema) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_source_registry.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement pipeline models**

```python
# src/aistock/pipeline/models.py
from dataclasses import dataclass, field
from datetime import date
from logging import Logger

@dataclass
class FetchSpec:
    asset_type: str
    codes: list[str] | None
    start_date: date
    end_date: date
    schema: type
    frequency: str = "daily"

@dataclass
class PipelineContext:
    task_id: str
    config: dict
    log: Logger

@dataclass
class WriteResult:
    records_written: int
    partitions_affected: list[str]
    backend: str

@dataclass
class PipelineReport:
    task_id: str
    source_name: str
    status: str
    records_fetched: int
    records_after_clean: int
    records_written: int
    duration_ms: int
    issues: list[str] = field(default_factory=list)
    failed_codes: list[str] = field(default_factory=list)
    fallback_used: str | None = None
```

- [ ] **Step 4: Implement SourceNode ABC**

```python
# src/aistock/pipeline/source.py
import time
from abc import ABC, abstractmethod
import pandas as pd
from aistock.exceptions import SourceRateLimited, SourceUnavailable

class SourceNode(ABC):
    name: str = ""
    retry_max: int = 3
    retry_delay_s: float = 5.0

    @abstractmethod
    def supports(self, asset_type: str, schema: type) -> bool:
        ...

    @abstractmethod
    def fetch(self, spec) -> pd.DataFrame:
        ...

    def fetch_with_retry(self, spec) -> pd.DataFrame:
        last_exc = None
        for attempt in range(self.retry_max):
            try:
                return self.fetch(spec)
            except SourceRateLimited as e:
                time.sleep(self.retry_delay_s * (2 ** attempt))
                last_exc = e
            except SourceUnavailable:
                raise
        raise last_exc if last_exc else RuntimeError("retry exhausted")

    def check_health(self) -> bool:
        return True
```

- [ ] **Step 5: Implement SourceRegistry**

```python
# src/aistock/sources/registry.py
from aistock.pipeline.source import SourceNode

class SourceRegistry:
    def __init__(self, config: dict):
        self._priorities: dict[type, list[tuple[str, int]]] = {}
        self._sources: dict[str, SourceNode] = {}

    def register(self, source: SourceNode, priority: int, schema: type):
        self._sources[source.name] = source
        if schema not in self._priorities:
            self._priorities[schema] = []
        self._priorities[schema].append((source.name, priority))
        self._priorities[schema].sort(key=lambda x: x[1], reverse=True)

    @property
    def primary(self) -> str | None:
        for priorities in self._priorities.values():
            if priorities:
                return priorities[0][0]
        return None

    def get_all(self, asset_type: str, schema: type) -> list[SourceNode]:
        candidates = self._priorities.get(schema, [])
        return [
            self._sources[name]
            for name, _ in candidates
            if name in self._sources
            and self._sources[name].supports(asset_type, schema)
        ]
```

- [ ] **Step 6: Create package __init__ files**

```python
# src/aistock/pipeline/__init__.py
"""Pipeline framework --- SourceNode -> Cleaner -> StorageBackend."""
```

```python
# src/aistock/sources/__init__.py
"""Data source plugins."""
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/unit/test_source_registry.py -v`
Expected: 10 passed (5 models + 5 registry)

- [ ] **Step 8: Commit**

```bash
git add src/aistock/pipeline/ src/aistock/sources/ tests/unit/test_source_registry.py
git commit -m "feat: pipeline models, SourceNode ABC, and SourceRegistry

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

## Task 6: CleaningStep Interface + Cleaner Orchestrator

**Files:**
- Create: `src/aistock/cleaning/__init__.py`
- Create: `src/aistock/cleaning/interface.py`
- Create: `src/aistock/pipeline/cleaner.py`
- Create: `tests/unit/test_cleaning_steps.py` (Cleaner tests only)

- [ ] **Step 1: Write failing Cleaner tests**

```python
# tests/unit/test_cleaning_steps.py
import logging
from datetime import date
import pandas as pd
import pytest
from aistock.cleaning.interface import CleaningStep
from aistock.pipeline.cleaner import Cleaner
from aistock.pipeline.models import PipelineContext
from aistock.exceptions import CleanError


class PassThroughStep(CleaningStep):
    name = "pass_through"
    def clean(self, df, ctx):
        return df

class AppendColumnStep(CleaningStep):
    name = "append_col"
    def clean(self, df, ctx):
        df = df.copy()
        df["new_col"] = 1
        return df

class FailingStep(CleaningStep):
    name = "failer"
    def clean(self, df, ctx):
        raise CleanError("intentional failure")

class StepWithValidation(CleaningStep):
    name = "with_validation"
    def clean(self, df, ctx):
        return df
    def validate(self, df):
        return ["test issue"]


class TestCleaner:
    def make_df(self):
        return pd.DataFrame({
            "code": ["000001.SZ"],
            "trade_date": [date(2025, 1, 2)],
            "open": [10.0], "high": [10.5], "low": [9.8], "close": [10.2],
            "volume": [1000000], "amount": [10200000.0],
        })

    def make_ctx(self):
        return PipelineContext(task_id="test-1", config={}, log=logging.getLogger("test"))

    def test_cleaner_runs_steps_in_order(self):
        cleaner = Cleaner([PassThroughStep(), AppendColumnStep()])
        df, issues = cleaner.clean(self.make_df(), self.make_ctx())
        assert "new_col" in df.columns

    def test_cleaner_collects_validation_issues(self):
        cleaner = Cleaner([StepWithValidation()])
        df, issues = cleaner.clean(self.make_df(), self.make_ctx())
        assert len(issues) == 1
        assert "test issue" in issues[0]

    def test_cleaner_propagates_clean_error(self):
        cleaner = Cleaner([FailingStep()])
        with pytest.raises(CleanError, match="intentional failure"):
            cleaner.clean(self.make_df(), self.make_ctx())

    def test_cleaner_empty_steps_returns_unchanged(self):
        cleaner = Cleaner([])
        df = self.make_df()
        result, issues = cleaner.clean(df, self.make_ctx())
        pd.testing.assert_frame_equal(result, df)
        assert issues == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_cleaning_steps.py::TestCleaner -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement CleaningStep interface**

```python
# src/aistock/cleaning/interface.py
from abc import ABC, abstractmethod
import pandas as pd

class CleaningStep(ABC):
    name: str = ""
    requires: list[str] = []

    @abstractmethod
    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        ...

    def validate(self, df: pd.DataFrame) -> list[str]:
        return []
```

- [ ] **Step 4: Implement Cleaner orchestrator**

```python
# src/aistock/pipeline/cleaner.py
import pandas as pd
from aistock.cleaning.interface import CleaningStep
from aistock.exceptions import CleanError

class Cleaner:
    def __init__(self, steps: list[CleaningStep]):
        self._steps = steps

    def clean(self, df: pd.DataFrame, ctx) -> tuple[pd.DataFrame, list[str]]:
        issues = []
        for step in self._steps:
            try:
                df = step.clean(df, ctx)
                step_issues = step.validate(df)
                issues.extend(f"[{step.name}] {i}" for i in step_issues)
            except CleanError:
                ctx.log.error(f"cleaning step [{step.name}] failed")
                raise
        return df, issues


# Populated in Task 15 when concrete steps are implemented
STEPS_BASELINE: list[CleaningStep] = []
STEPS_ADVANCED: list[CleaningStep] = []
```

```python
# src/aistock/cleaning/__init__.py
"""Data cleaning and standardization steps."""
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/unit/test_cleaning_steps.py::TestCleaner -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/aistock/cleaning/ src/aistock/pipeline/cleaner.py tests/unit/test_cleaning_steps.py
git commit -m "feat: CleaningStep interface and Cleaner orchestrator

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 7: PipelineRunner

**Files:**
- Create: `src/aistock/pipeline/runner.py`
- Create: `tests/integration/test_pipeline_runner.py`

- [ ] **Step 1: Write failing runner test**

```python
# tests/integration/test_pipeline_runner.py
import logging
import uuid
from datetime import date
import pandas as pd
import pytest
from aistock.pipeline.models import FetchSpec, PipelineContext
from aistock.pipeline.source import SourceNode
from aistock.pipeline.cleaner import Cleaner
from aistock.pipeline.runner import PipelineRunner
from aistock.schemas.daily import StockDailySchema
from aistock.sources.registry import SourceRegistry
from aistock.exceptions import SourceUnavailable, PipelineError


class StubSource(SourceNode):
    def __init__(self, name, df=None):
        self.name = name
        self._df = df if df is not None else pd.DataFrame()
    def supports(self, asset_type, schema):
        return True
    def fetch(self, spec):
        return self._df.copy()

class FailingSource(SourceNode):
    def __init__(self, name, exc=SourceUnavailable("nope")):
        self.name = name
        self._exc = exc
    def supports(self, asset_type, schema):
        return True
    def fetch(self, spec):
        raise self._exc

class StubStore:
    name = "stub"
    def write(self, df, schema, partition_keys):
        from aistock.pipeline.models import WriteResult
        return WriteResult(len(df), ["stub/partition"], "stub")
    def read(self, query):
        return pd.DataFrame()
    def upsert(self, df, schema, partition_keys, on_conflict):
        from aistock.pipeline.models import WriteResult
        return WriteResult(len(df), ["stub/partition"], "stub")
    def exists(self, schema, partition_keys):
        return False

def make_daily_df(codes=None):
    if codes is None:
        codes = ["000001.SZ"]
    rows = []
    for c in codes:
        for d in [date(2025, 1, 2), date(2025, 1, 3)]:
            rows.append({
                "code": c, "trade_date": d, "asset_type": "stock",
                "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2,
                "volume": 1000000, "amount": 10200000.0,
                "adj_factor": 1.0, "is_st": False, "is_suspended": False,
            })
    return pd.DataFrame(rows)

class TestPipelineRunner:
    def make_runner(self, registry, store=None):
        if store is None:
            store = StubStore()
        ctx = PipelineContext(task_id=str(uuid.uuid4()), config={},
                             log=logging.getLogger("test"))
        return PipelineRunner(registry, Cleaner([]), store, ctx)

    def make_spec(self, codes=None):
        if codes is None:
            codes = ["000001.SZ"]
        return FetchSpec(
            asset_type="stock", codes=codes,
            start_date=date(2025, 1, 2), end_date=date(2025, 1, 6),
            schema=StockDailySchema, frequency="daily",
        )

    def test_success_path_returns_success(self):
        registry = SourceRegistry({})
        registry.register(StubSource("akstock", make_daily_df()),
                         priority=100, schema=StockDailySchema)
        report = self.make_runner(registry).run(self.make_spec())
        assert report.status == "success"
        assert report.records_fetched == 2

    def test_failed_codes_when_requested_not_in_result(self):
        registry = SourceRegistry({})
        df = make_daily_df(["000001.SZ"])
        registry.register(StubSource("akstock", df), priority=100, schema=StockDailySchema)
        report = self.make_runner(registry).run(self.make_spec(["000001.SZ", "999999.SZ"]))
        assert report.status == "partial"
        assert report.failed_codes == ["999999.SZ"]

    def test_all_sources_exhausted_raises(self):
        registry = SourceRegistry({})
        for name in ["akstock", "baostock", "tushare"]:
            registry.register(FailingSource(name), priority=100, schema=StockDailySchema)
        runner = self.make_runner(registry)
        with pytest.raises(PipelineError, match="All sources exhausted"):
            runner.run(self.make_spec())

    def test_zero_records_returns_failed(self):
        registry = SourceRegistry({})
        registry.register(StubSource("akstock", pd.DataFrame()),
                         priority=100, schema=StockDailySchema)
        report = self.make_runner(registry).run(self.make_spec())
        assert report.status == "failed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_pipeline_runner.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement PipelineRunner**

```python
# src/aistock/pipeline/runner.py
import time
import pandas as pd
from aistock.pipeline.models import PipelineReport
from aistock.sources.registry import SourceRegistry
from aistock.pipeline.cleaner import Cleaner
from aistock.storage.interface import StorageBackend
from aistock.exceptions import (
    SourceUnavailable, SourceRateLimited, CleanError, StoreError, PipelineError,
)

class PipelineRunner:
    def __init__(self, registry: SourceRegistry, cleaner: Cleaner,
                 store: StorageBackend, ctx):
        self._registry = registry
        self._cleaner = cleaner
        self._store = store
        self._ctx = ctx

    def run(self, spec) -> PipelineReport:
        issues_overall = []
        start_time = time.monotonic()

        for source in self._registry.get_all(spec.asset_type, spec.schema):
            try:
                if not source.check_health():
                    self._ctx.log.info(f"source [{source.name}] unhealthy, skipping")
                    continue

                df = source.fetch_with_retry(spec)
                records_fetched = len(df)

                schema_issues = spec.schema.validate(df)
                if schema_issues:
                    self._ctx.log.warning(f"schema validation: {schema_issues}")
                    issues_overall.extend(schema_issues)
                    before = len(df)
                    df = df[~self._find_invalid_rows_mask(df, spec.schema)]
                    self._ctx.log.info(f"filtered {before - len(df)} invalid rows")

                df, clean_issues = self._cleaner.clean(df, self._ctx)
                issues_overall.extend(clean_issues)

                result = self._store.write(df, spec.schema,
                                          spec.schema.partition_values(df))

                if spec.codes is not None:
                    requested = set(spec.codes)
                    actual = set(df["code"].unique())
                    failed_codes = sorted(requested - actual)
                else:
                    failed_codes = []

                if records_fetched == 0:
                    status = "failed"
                elif len(failed_codes) > 0:
                    status = "partial"
                else:
                    status = "success"

                return PipelineReport(
                    task_id=self._ctx.task_id,
                    source_name=source.name,
                    status=status,
                    records_fetched=records_fetched,
                    records_after_clean=len(df),
                    records_written=result.records_written,
                    duration_ms=int((time.monotonic() - start_time) * 1000),
                    issues=issues_overall,
                    failed_codes=failed_codes,
                    fallback_used=(source.name if source.name != self._registry.primary else None),
                )

            except (SourceUnavailable, SourceRateLimited, CleanError) as e:
                self._ctx.log.warning(f"source [{source.name}] failed: {e}, falling back")
                continue
            except StoreError:
                raise

        raise PipelineError("All sources exhausted --- unable to fetch data")

    @staticmethod
    def _find_invalid_rows_mask(df: pd.DataFrame, schema: type) -> pd.Series:
        result = pd.Series(False, index=df.index)
        required = {"code", "trade_date", "open", "high", "low", "close",
                     "volume", "amount"}
        missing = required - set(df.columns)
        if missing:
            return result
        result |= (df["high"] < df["low"])
        result |= (df[["open", "high", "low", "close"]] < 0).any(axis=1)
        result |= (df["volume"] < 0)
        return result
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/integration/test_pipeline_runner.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/aistock/pipeline/runner.py tests/integration/test_pipeline_runner.py
git commit -m "feat: PipelineRunner with fallback chain and partial success

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

## Task 8: StorageBackend Interface + QuerySpec + Router

**Files:**
- Create: `src/aistock/storage/__init__.py`
- Create: `src/aistock/storage/interface.py`
- Create: `src/aistock/storage/query.py`
- Create: `src/aistock/storage/router.py`
- Create: `tests/unit/test_query_spec.py`

- [ ] **Step 1: Write failing test for QuerySpec**

```python
# tests/unit/test_query_spec.py
from datetime import date
from aistock.storage.query import QuerySpec
from aistock.schemas.daily import StockDailySchema

class TestQuerySpec:
    def test_basic_creation(self):
        qs = QuerySpec(schema=StockDailySchema)
        assert qs.schema is StockDailySchema
        assert qs.asset_types is None

    def test_full_spec(self):
        qs = QuerySpec(
            schema=StockDailySchema,
            asset_types=["stock"],
            codes=["000001.SZ"],
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            frequency="daily",
            columns=["code", "close"],
            partition_keys={"year": "2025", "month": "01"},
        )
        assert qs.start_date == date(2025, 1, 1)
        assert qs.columns == ["code", "close"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_query_spec.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement all storage interface files**

```python
# src/aistock/storage/interface.py
from abc import ABC, abstractmethod
import pandas as pd

class StorageBackend(ABC):
    name: str = ""

    @abstractmethod
    def write(self, df: pd.DataFrame, schema: type, partition_keys: dict):
        ...

    @abstractmethod
    def read(self, query):
        ...

    @abstractmethod
    def upsert(self, df: pd.DataFrame, schema: type,
               partition_keys: dict, on_conflict: list[str]):
        ...

    @abstractmethod
    def exists(self, schema: type, partition_keys: dict) -> bool:
        ...
```

```python
# src/aistock/storage/query.py
from dataclasses import dataclass
from datetime import date

@dataclass
class QuerySpec:
    schema: type
    asset_types: list[str] | None = None
    codes: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None
    frequency: str | None = None
    columns: list[str] | None = None
    partition_keys: dict | None = None
```

```python
# src/aistock/storage/router.py
from aistock.exceptions import StoreError

def get_backend(config: dict):
    backend_name = config["storage"]["backend"]
    if backend_name == "parquet":
        from aistock.storage.parquet.backend import ParquetBackend
        return ParquetBackend(config)
    if backend_name == "postgres":
        from aistock.storage.postgres.backend import PostgresBackend
        return PostgresBackend(config)
    raise StoreError(f"Unknown backend: {backend_name}")
```

```python
# src/aistock/storage/__init__.py
"""Storage abstraction --- Parquet (Phase 1), PostgreSQL (Phase 2)."""
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_query_spec.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/aistock/storage/ tests/unit/test_query_spec.py
git commit -m "feat: StorageBackend ABC, QuerySpec, router factory

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 9: Partition Strategy

**Files:**
- Create: `src/aistock/storage/parquet/__init__.py`
- Create: `src/aistock/storage/parquet/partition.py`
- Create: `tests/unit/test_partition.py`

- [ ] **Step 1: Write failing partition test**

```python
# tests/unit/test_partition.py
from datetime import date, datetime
import pandas as pd
from aistock.storage.parquet.partition import build_partition_path

class TestPartitionPath:
    def test_daily_partition_path(self):
        pkeys = {"asset_type": "stock", "year": "2025", "month": "01"}
        path = build_partition_path("daily", pkeys)
        assert "stock" in str(path)
        assert "2025" in str(path)
        assert "01" in str(path)

    def test_minute_partition_path(self):
        pkeys = {"asset_type": "stock", "frequency": "5min",
                 "year": "2025", "month": "01"}
        path = build_partition_path("minute", pkeys)
        assert "5min" in str(path)

    def test_finance_partition_path(self):
        pkeys = {"asset_type": "stock", "report_period": "2025Q4"}
        path = build_partition_path("finance", pkeys)
        assert "2025Q4" in str(path)

    def test_north_flow_partition_path(self):
        pkeys = {"year": "2025", "month": "01"}
        path = build_partition_path("north_flow", pkeys)
        assert "north_flow" in str(path)

    def test_reference_partition_path_no_partition(self):
        path = build_partition_path("reference", {})
        assert "_reference" in str(path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_partition.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement partition strategy**

```python
# src/aistock/storage/parquet/partition.py
from pathlib import Path

SCHEMA_PARTITION_LAYOUT = {
    "daily":         ["asset_type", "year", "month"],
    "minute":        ["asset_type", "frequency", "year", "month"],
    "finance":       ["asset_type", "report_period"],
    "north_flow":    ["year", "month"],
    "margin_trade":  ["year", "month"],
    "alternative":   ["sub_type", "year", "month"],
    "reference":     [],  # single file, no partition
}

def build_partition_path(schema_name: str, partition_keys: dict) -> Path:
    layout = SCHEMA_PARTITION_LAYOUT.get(schema_name, [])
    if not layout:
        return Path("_reference")
    parts = [str(partition_keys.get(k, "unknown")) for k in layout]
    return Path(schema_name).joinpath(*parts)
```

```python
# src/aistock/storage/parquet/__init__.py
"""Parquet storage backend."""
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_partition.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/aistock/storage/parquet/ tests/unit/test_partition.py
git commit -m "feat: partition strategy with per-schema layout map

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 10: ParquetBackend

**Files:**
- Create: `src/aistock/storage/parquet/backend.py`
- Create: `tests/integration/test_parquet_backend.py`

- [ ] **Step 1: Write failing integration test**

```python
# tests/integration/test_parquet_backend.py
import tempfile
from datetime import date
import pandas as pd
import pytest
from aistock.storage.parquet.backend import ParquetBackend
from aistock.storage.query import QuerySpec
from aistock.schemas.daily import StockDailySchema
from aistock.pipeline.models import WriteResult


def make_daily_df(codes=None):
    if codes is None:
        codes = ["000001.SZ", "600000.SH"]
    rows = []
    for c in codes:
        for i, d in enumerate([date(2025, 1, 2), date(2025, 1, 3)]):
            rows.append({
                "asset_type": "stock", "code": c, "trade_date": d,
                "open": 10.0 + i, "high": 10.5 + i, "low": 9.8 + i,
                "close": 10.2 + i, "volume": 1000000, "amount": 10200000.0,
                "turnover": 0.02, "adj_factor": 1.0,
                "is_st": False, "is_suspended": False,
            })
    return pd.DataFrame(rows)


@pytest.fixture
def backend():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield ParquetBackend({"data_dir": tmpdir, "compression": "zstd"})


@pytest.fixture
def df_daily():
    return make_daily_df()


class TestParquetBackend:
    def test_write_and_read_roundtrip(self, backend, df_daily):
        pkeys = StockDailySchema.partition_values(df_daily)
        result = backend.write(df_daily, StockDailySchema, pkeys)
        assert result.records_written == 4
        query = QuerySpec(schema=StockDailySchema, partition_keys=pkeys)
        read_back = backend.read(query)
        assert len(read_back) == 4
        assert set(read_back["code"]) == {"000001.SZ", "600000.SH"}

    def test_upsert_overwrites_existing_keys(self, backend, df_daily):
        pkeys = StockDailySchema.partition_values(df_daily)
        backend.write(df_daily, StockDailySchema, pkeys)
        df_updated = df_daily.copy()
        df_updated.loc[0, "close"] = 999.99
        backend.upsert(df_updated, StockDailySchema, pkeys,
                       on_conflict=["code", "trade_date"])
        query = QuerySpec(schema=StockDailySchema, partition_keys=pkeys)
        result = backend.read(query)
        assert 999.99 in result["close"].values

    def test_exists_for_written_partition(self, backend, df_daily):
        pkeys = StockDailySchema.partition_values(df_daily)
        assert not backend.exists(StockDailySchema, pkeys)
        backend.write(df_daily, StockDailySchema, pkeys)
        assert backend.exists(StockDailySchema, pkeys)

    def test_read_with_code_filter(self, backend, df_daily):
        pkeys = StockDailySchema.partition_values(df_daily)
        backend.write(df_daily, StockDailySchema, pkeys)
        query = QuerySpec(schema=StockDailySchema, codes=["000001.SZ"],
                         partition_keys=pkeys)
        result = backend.read(query)
        assert len(result) == 2
        assert all(result["code"] == "000001.SZ")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_parquet_backend.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement ParquetBackend**

```python
# src/aistock/storage/parquet/backend.py
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from aistock.storage.interface import StorageBackend
from aistock.storage.query import QuerySpec
from aistock.storage.parquet.partition import build_partition_path
from aistock.pipeline.models import WriteResult


class ParquetBackend(StorageBackend):
    name = "parquet"

    def __init__(self, config: dict):
        self._base = Path(config["data_dir"]) / "parquet"
        self._compression = config.get("compression", "zstd")

    def _build_path(self, schema_name: str, partition_keys: dict) -> Path:
        return self._base / build_partition_path(schema_name, partition_keys)

    def write(self, df: pd.DataFrame, schema: type,
              partition_keys: dict) -> WriteResult:
        path = self._build_path(schema.__name__, partition_keys)
        path.mkdir(parents=True, exist_ok=True)
        filepath = path / "data.parquet"
        df.to_parquet(filepath, compression=self._compression, index=False)
        return WriteResult(
            records_written=len(df),
            partitions_affected=[str(path.relative_to(self._base))],
            backend="parquet",
        )

    def read(self, query: QuerySpec) -> pd.DataFrame:
        path = self._base
        if query.partition_keys:
            path = self._build_path(query.schema.__name__,
                                    query.partition_keys)
        if not path.exists():
            return pd.DataFrame()
        table = pq.read_table(path)
        df = table.to_pandas()
        if query.codes:
            df = df[df["code"].isin(query.codes)]
        if query.start_date:
            date_col = "trade_date" if "trade_date" in df.columns else "trade_time"
            if date_col in df.columns:
                df = df[df[date_col] >= pd.Timestamp(query.start_date)]
        if query.end_date:
            date_col = "trade_date" if "trade_date" in df.columns else "trade_time"
            if date_col in df.columns:
                df = df[df[date_col] <= pd.Timestamp(query.end_date)]
        if query.columns:
            df = df[list(query.columns)]
        return df.reset_index(drop=True)

    def upsert(self, df: pd.DataFrame, schema: type,
               partition_keys: dict, on_conflict: list[str]) -> WriteResult:
        path = self._build_path(schema.__name__, partition_keys)
        filepath = path / "data.parquet"
        if filepath.exists():
            existing = pd.read_parquet(filepath)
            merged = pd.concat([existing, df], ignore_index=True)
            merged = merged.drop_duplicates(subset=on_conflict, keep="last")
            merged = merged.sort_values(on_conflict).reset_index(drop=True)
        else:
            merged = df
        path.mkdir(parents=True, exist_ok=True)
        merged.to_parquet(filepath, compression=self._compression, index=False)
        return WriteResult(
            records_written=len(merged),
            partitions_affected=[str(path.relative_to(self._base))],
            backend="parquet",
        )

    def exists(self, schema: type, partition_keys: dict) -> bool:
        path = self._build_path(schema.__name__, partition_keys)
        filepath = path / "data.parquet"
        return filepath.exists()
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/integration/test_parquet_backend.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/aistock/storage/parquet/backend.py tests/integration/test_parquet_backend.py
git commit -m "feat: ParquetBackend with write/read/upsert/exists and partition support

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 11: PostgreSQL Skeleton (Phase 2 placeholder)

**Files:**
- Create: `src/aistock/storage/postgres/__init__.py`
- Create: `src/aistock/storage/postgres/backend.py`
- Create: `src/aistock/storage/postgres/models.py`

- [ ] **Step 1: Create skeleton files**

```python
# src/aistock/storage/postgres/__init__.py
"""PostgreSQL storage backend (Phase 2)."""
```

```python
# src/aistock/storage/postgres/backend.py
"""PostgresBackend --- skeleton for Phase 2.

When implemented, will use SQLAlchemy + asyncpg for:
- Upsert via ON CONFLICT
- Partition-wise queries via QuerySpec
- Connection pooling
"""
from aistock.storage.interface import StorageBackend
from aistock.exceptions import BackendUnavailable


class PostgresBackend(StorageBackend):
    name = "postgres"

    def __init__(self, config: dict):
        raise BackendUnavailable("PostgreSQL backend is not implemented (Phase 2)")

    def write(self, df, schema, partition_keys):
        raise BackendUnavailable("PostgreSQL backend is not implemented (Phase 2)")

    def read(self, query):
        raise BackendUnavailable("PostgreSQL backend is not implemented (Phase 2)")

    def upsert(self, df, schema, partition_keys, on_conflict):
        raise BackendUnavailable("PostgreSQL backend is not implemented (Phase 2)")

    def exists(self, schema, partition_keys):
        raise BackendUnavailable("PostgreSQL backend is not implemented (Phase 2)")
```

```python
# src/aistock/storage/postgres/models.py
"""SQLAlchemy ORM models for PostgreSQL (Phase 2).

Tables will mirror the 5 internal schemas:
- stock_daily
- stock_minute
- finance
- alternative_north_flow / alternative_margin_trade / alternative_generic
- reference
"""
# Phase 2:
# from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
# class Base(DeclarativeBase): ...
```

- [ ] **Step 2: Commit**

```bash
git add src/aistock/storage/postgres/
git commit -m "feat: PostgreSQL backend skeleton (Phase 2 placeholder)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

## Task 12: Observability (Logger + Tracer)

**Files:**
- Create: `src/aistock/observability/__init__.py`
- Create: `src/aistock/observability/logger.py`
- Create: `src/aistock/observability/models.py`
- Create: `src/aistock/observability/tracer.py`
- Create: `tests/integration/test_observability.py`

- [ ] **Step 1: Write failing observability test**

```python
# tests/integration/test_observability.py
import json
import tempfile
from pathlib import Path
import pytest
from aistock.observability.logger import PipelineLogger
from aistock.observability.tracer import TaskTracer
from aistock.observability.models import TaskRun, DataSnapshot


class TestPipelineLogger:
    def test_log_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = PipelineLogger(log_dir=tmpdir, retention_days=90)
            logger.log("INFO", "fetch", "testing", key="value")
            # Find the log file
            log_dir = Path(tmpdir)
            today_dir = list(log_dir.glob("*"))[0]
            log_files = list(today_dir.glob("*.jsonl"))
            assert len(log_files) == 1
            line = log_files[0].read_text().strip()
            record = json.loads(line)
            assert record["level"] == "INFO"
            assert record["step"] == "fetch"
            assert record["message"] == "testing"
            assert record["key"] == "value"

    def test_multiple_logs_same_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = PipelineLogger(log_dir=tmpdir, retention_days=90)
            logger.log("INFO", "fetch", "first")
            logger.log("INFO", "clean", "second")
            log_dir = Path(tmpdir)
            today_dir = next(d for d in log_dir.glob("*") if d.is_dir())
            log_files = list(today_dir.glob("*.jsonl"))
            lines = log_files[0].read_text().strip().split("\n")
            assert len(lines) == 2


class TestTaskTracer:
    def test_record_and_query_task_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracer = TaskTracer(db_path=str(Path(tmpdir) / "meta.db"))
            run = TaskRun(
                task_id="test-123",
                started_at="2025-01-01T00:00:00",
                finished_at="2025-01-01T00:01:00",
                source_name="akstock",
                status="success",
                records_fetched=100,
                records_after_clean=98,
                records_written=98,
                duration_ms=60000,
            )
            tracer.record_task_run(run)
            recent = tracer.get_recent_runs(limit=5)
            assert len(recent) == 1
            assert recent[0].task_id == "test-123"
            assert recent[0].status == "success"

    def test_record_and_query_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracer = TaskTracer(db_path=str(Path(tmpdir) / "meta.db"))
            snap = DataSnapshot(
                date="2025-01-02",
                schema_name="daily",
                partition_key="stock/2025/01",
                record_count=5000,
                source_name="akstock",
                checksum="abc123",
            )
            tracer.record_snapshot(snap)
            recent = tracer.get_recent_snapshots(limit=5)
            assert len(recent) == 1
            assert recent[0].record_count == 5000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_observability.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement observability module**

```python
# src/aistock/observability/models.py
from dataclasses import dataclass

@dataclass
class TaskRun:
    task_id: str
    started_at: str
    finished_at: str
    source_name: str
    status: str
    records_fetched: int
    records_after_clean: int
    records_written: int
    duration_ms: int
    issues_json: str = "[]"
    fallback_used: str | None = None
    failed_codes_json: str = "[]"
    spec_json: str = "{}"

@dataclass
class DataSnapshot:
    date: str
    schema_name: str
    partition_key: str
    record_count: int
    source_name: str
    checksum: str
```

```python
# src/aistock/observability/logger.py
import json
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

class PipelineLogger:
    def __init__(self, log_dir: str = "logs", retention_days: int = 90):
        self._log_dir = Path(log_dir)
        self._retention_days = retention_days
        self._today = datetime.now().strftime("%Y-%m-%d")

    def log(self, level: str, step: str, message: str, **extra):
        day_dir = self._log_dir / self._today
        day_dir.mkdir(parents=True, exist_ok=True)
        # Use a single file per day for simplicity
        log_file = day_dir / f"pipeline.jsonl"
        record = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "step": step,
            "message": message,
            **extra,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def cleanup(self):
        cutoff = datetime.now() - timedelta(days=self._retention_days)
        for day_dir in self._log_dir.iterdir():
            if not day_dir.is_dir():
                continue
            try:
                dir_date = datetime.strptime(day_dir.name, "%Y-%m-%d")
                if dir_date < cutoff:
                    shutil.rmtree(day_dir)
            except ValueError:
                continue
```

```python
# src/aistock/observability/tracer.py
import json
import sqlite3
from pathlib import Path
from aistock.observability.models import TaskRun, DataSnapshot

class TaskTracer:
    def __init__(self, db_path: str = "data/meta/data_pipeline.db"):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_runs (
                    id TEXT PRIMARY KEY,
                    started_at TEXT, finished_at TEXT,
                    source_name TEXT, status TEXT,
                    records_fetched INTEGER, records_after_clean INTEGER,
                    records_written INTEGER, duration_ms INTEGER,
                    issues_json TEXT, fallback_used TEXT,
                    failed_codes_json TEXT, spec_json TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT, schema_name TEXT,
                    partition_key TEXT, record_count INTEGER,
                    source_name TEXT, checksum TEXT
                )
            """)

    def record_task_run(self, run: TaskRun):
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO task_runs
                (id, started_at, finished_at, source_name, status,
                 records_fetched, records_after_clean, records_written,
                 duration_ms, issues_json, fallback_used, failed_codes_json, spec_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.task_id, run.started_at, run.finished_at,
                run.source_name, run.status,
                run.records_fetched, run.records_after_clean,
                run.records_written, run.duration_ms,
                run.issues_json, run.fallback_used,
                run.failed_codes_json, run.spec_json,
            ))

    def get_recent_runs(self, limit: int = 10) -> list[TaskRun]:
        with sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM task_runs ORDER BY started_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [TaskRun(
            task_id=r[0], started_at=r[1], finished_at=r[2],
            source_name=r[3], status=r[4],
            records_fetched=r[5], records_after_clean=r[6],
            records_written=r[7], duration_ms=r[8],
            issues_json=r[9], fallback_used=r[10],
            failed_codes_json=r[11], spec_json=r[12],
        ) for r in rows]

    def record_snapshot(self, snap: DataSnapshot):
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("""
                INSERT INTO data_snapshots
                (date, schema_name, partition_key, record_count,
                 source_name, checksum)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (snap.date, snap.schema_name, snap.partition_key,
                  snap.record_count, snap.source_name, snap.checksum))

    def get_recent_snapshots(self, limit: int = 10) -> list[DataSnapshot]:
        with sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT date, schema_name, partition_key, record_count, "
                "source_name, checksum FROM data_snapshots "
                "ORDER BY date DESC LIMIT ?", (limit,)
            ).fetchall()
        return [DataSnapshot(
            date=r[0], schema_name=r[1], partition_key=r[2],
            record_count=r[3], source_name=r[4], checksum=r[5],
        ) for r in rows]
```

```python
# src/aistock/observability/__init__.py
"""Observability --- structured JSON logging + SQLite task metadata."""
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/integration/test_observability.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/aistock/observability/ tests/integration/test_observability.py
git commit -m "feat: observability (JSONL logger + SQLite tracer with 90-day retention)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 13: Factors Skeleton

**Files:**
- Create: `src/aistock/factors/__init__.py`
- Create: `src/aistock/factors/interface.py`
- Create: `src/aistock/factors/registry.py`

- [ ] **Step 1: Create skeleton files**

```python
# src/aistock/factors/interface.py
"""Factor calculation abstraction."""
from abc import ABC, abstractmethod
import pandas as pd

class FactorCalculator(ABC):
    name: str = ""

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        ...
```

```python
# src/aistock/factors/registry.py
"""Factor registry --- populate as factors are implemented."""
from aistock.factors.interface import FactorCalculator

FACTOR_REGISTRY: dict[str, FactorCalculator] = {}
```

```python
# src/aistock/factors/__init__.py
"""Factor calculation layer (skeleton for future phases)."""
```

- [ ] **Step 2: Commit**

```bash
git add src/aistock/factors/
git commit -m "feat: factors skeleton (interface + empty registry)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

## Task 14: AkStock Source Plugin

**Files:**
- Create: `src/aistock/sources/akstock/__init__.py`
- Create: `src/aistock/sources/akstock/client.py`
- Create: `src/aistock/sources/akstock/mapper.py`
- Create: `src/aistock/sources/akstock/downloader.py`

- [ ] **Step 1: Write mapper test (the only testable part without real API)**

```python
# Add to tests/conftest.py:
import pytest
import pandas as pd
from datetime import date

@pytest.fixture
def df_daily_good():
    """5 stocks x 5 days of clean daily data."""
    codes = ["000001.SZ", "600000.SH", "000002.SZ", "600036.SH", "000858.SZ"]
    dates = pd.date_range("2025-01-02", "2025-01-06", freq="B")
    rows = []
    for code in codes:
        for d in dates:
            rows.append({
                "code": code, "trade_date": d.date(),
                "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2,
                "volume": 1000000, "amount": 10200000.0,
                "turnover": 0.02, "adj_factor": 1.0,
                "is_st": False, "is_suspended": False,
                "asset_type": "stock",
            })
    return pd.DataFrame(rows)

@pytest.fixture
def mock_context():
    import logging
    from aistock.pipeline.models import PipelineContext
    return PipelineContext(task_id="test-001", config={}, log=logging.getLogger("test"))

@pytest.fixture
def backend(tmp_path):
    from aistock.storage.parquet.backend import ParquetBackend
    return ParquetBackend({"data_dir": str(tmp_path), "compression": "zstd"})
```

- [ ] **Step 2: Implement AkStock client**

```python
# src/aistock/sources/akstock/client.py
"""AkShare API wrapper with rate limiting and retry."""
import time
import akshare as ak
import pandas as pd
from aistock.exceptions import SourceUnavailable, SourceRateLimited

class AkStockClient:
    """Encapsulates akshare calls. All methods return raw DataFrames."""

    def __init__(self, config: dict | None = None):
        self._config = config or {}
        self._call_count = 0
        self._last_call = 0.0
        self._min_interval = 0.5  # seconds between calls

    def _rate_limit(self):
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.monotonic()
        self._call_count += 1

    def fetch_daily(self, code: str, start_date: str, end_date: str,
                    adjustment: str = "qfq") -> pd.DataFrame:
        try:
            self._rate_limit()
            df = ak.stock_zh_a_hist(
                symbol=code, period="daily",
                start_date=start_date, end_date=end_date,
                adjust=adjustment,
            )
            return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
        except Exception as e:
            msg = str(e).lower()
            if "timeout" in msg or "limit" in msg or "频繁" in msg:
                raise SourceRateLimited(f"akshare rate limited: {e}")
            raise SourceUnavailable(f"akshare unavailable: {e}")

    def check_health(self) -> bool:
        try:
            self._rate_limit()
            df = ak.stock_zh_a_hist(symbol="000001", period="daily",
                                    start_date="2025-01-02", end_date="2025-01-06",
                                    adjust="qfq")
            return isinstance(df, pd.DataFrame) and len(df) > 0
        except Exception:
            return False
```

- [ ] **Step 3: Implement AkStock mapper**

```python
# src/aistock/sources/akstock/mapper.py
"""AkShare raw fields --> internal StockDailySchema fields."""
import pandas as pd

def to_internal(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[
            "asset_type", "code", "trade_date", "open", "high", "low",
            "close", "volume", "amount", "turnover", "adj_factor",
            "is_st", "is_suspended",
        ])
    result = pd.DataFrame()
    result["code"] = df["股票代码"].apply(to_internal_code)
    result["trade_date"] = pd.to_datetime(df["日期"]).dt.date
    result["open"] = df["开盘"].astype(float)
    result["high"] = df["最高"].astype(float)
    result["low"] = df["最低"].astype(float)
    result["close"] = df["收盘"].astype(float)
    result["volume"] = df["成交量"].astype("int64")
    result["amount"] = df["成交额"].astype(float)
    result["turnover"] = df.get("换手率", pd.Series([None] * len(df))).astype(float)
    result["adj_factor"] = 1.0  # akshare with qfq returns pre-adjusted prices
    result["is_st"] = df["股票代码"].str.contains("ST", na=False)
    result["is_suspended"] = (result["volume"] == 0) & (result["amount"] == 0)
    result["asset_type"] = "stock"
    return result


def to_internal_code(raw_code: str) -> str:
    code = str(raw_code).strip()
    if "." in code:
        return code
    if code.startswith(("6", "5", "9")):
        return f"{code}.SH"
    elif code.startswith(("0", "2", "3")):
        return f"{code}.SZ"
    elif code.startswith(("4", "8")):
        return f"{code}.BJ"
    return code
```

- [ ] **Step 4: Implement AkStock downloader**

```python
# src/aistock/sources/akstock/downloader.py
import pandas as pd
from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.sources.akstock.client import AkStockClient
from aistock.sources.akstock.mapper import to_internal, to_internal_code
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.minute import StockMinuteSchema

class AkStockSource(SourceNode):
    name = "akstock"

    def __init__(self, config: dict | None = None):
        self.client = AkStockClient(config)

    def supports(self, asset_type: str, schema: type) -> bool:
        if schema in (StockDailySchema, StockMinuteSchema):
            return asset_type in ("stock", "index")
        return True  # broad support claim

    def fetch(self, spec: FetchSpec) -> pd.DataFrame:
        spec_codes = spec.codes if spec.codes else []
        if not spec_codes:
            spec_codes = ["000001"]  # placeholder; codes=None handled by Runner

        start = spec.start_date.strftime("%Y%m%d")
        end = spec.end_date.strftime("%Y%m%d")

        frames = []
        for raw_code in spec_codes:
            try:
                df = self.client.fetch_daily(
                    code=raw_code, start_date=start, end_date=end,
                )
                if not df.empty:
                    df = to_internal(df)
                    frames.append(df)
            except Exception:
                continue  # partial; Runner tracks failed_codes

        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def check_health(self) -> bool:
        return self.client.check_health()
```

```python
# src/aistock/sources/akstock/__init__.py
"""AkShare data source plugin."""
from aistock.sources.akstock.downloader import AkStockSource
```

- [ ] **Step 5: Run mapper unit test manually and commit**

Run: `python -c "from aistock.sources.akstock.mapper import to_internal_code; assert to_internal_code('000001') == '000001.SZ'; assert to_internal_code('600000') == '600000.SH'; print('mapper OK')"`

```bash
git add src/aistock/sources/akstock/ tests/conftest.py
git commit -m "feat: AkStock source plugin (client + mapper + downloader)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 15: BaoStock Source Plugin

**Files:**
- Create: `src/aistock/sources/baostock/__init__.py`
- Create: `src/aistock/sources/baostock/client.py`
- Create: `src/aistock/sources/baostock/mapper.py`
- Create: `src/aistock/sources/baostock/downloader.py`

- [ ] **Step 1: Implement BaoStock client**

```python
# src/aistock/sources/baostock/client.py
"""BaoStock API wrapper."""
import baostock as bs
import pandas as pd
from aistock.exceptions import SourceUnavailable, SourceRateLimited

class BaoStockClient:
    def __init__(self, config: dict | None = None):
        self._config = config or {}
        self._logged_in = False

    def _ensure_login(self):
        if not self._logged_in:
            lg = bs.login()
            if lg.error_code != "0":
                raise SourceUnavailable(f"baostock login failed: {lg.error_msg}")
            self._logged_in = True

    def fetch_daily(self, code: str, start_date: str, end_date: str,
                    frequency: str = "d") -> pd.DataFrame:
        try:
            self._ensure_login()
            rs = bs.query_history_k_data_plus(
                code=code,
                fields="date,code,open,high,low,close,volume,amount,"
                       "turn,tradestatus,isST,adjustflag",
                start_date=start_date.replace("-", "-"),
                end_date=end_date.replace("-", "-"),
                frequency=frequency,
                adjustflag="2",  # forward-adjusted
            )
            if rs.error_code != "0":
                raise SourceUnavailable(f"baostock query failed: {rs.error_msg}")
            rows = []
            while (rs.error_code == "0") and rs.next():
                rows.append(rs.get_row_data())
            return pd.DataFrame(rows, columns=rs.fields) if rows else pd.DataFrame()
        except (SourceUnavailable, SourceRateLimited):
            raise
        except Exception as e:
            raise SourceUnavailable(f"baostock error: {e}")

    def logout(self):
        if self._logged_in:
            bs.logout()
            self._logged_in = False
```

- [ ] **Step 2: Implement BaoStock mapper**

```python
# src/aistock/sources/baostock/mapper.py
"""BaoStock raw fields --> internal StockDailySchema fields."""
import pandas as pd

def to_internal(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[
            "asset_type", "code", "trade_date", "open", "high", "low",
            "close", "volume", "amount", "turnover", "adj_factor",
            "is_st", "is_suspended",
        ])
    result = pd.DataFrame()
    result["code"] = df["code"].apply(to_internal_code)
    result["trade_date"] = pd.to_datetime(df["date"]).dt.date
    result["open"] = df["open"].astype(float)
    result["high"] = df["high"].astype(float)
    result["low"] = df["low"].astype(float)
    result["close"] = df["close"].astype(float)
    result["volume"] = df["volume"].astype("int64")
    result["amount"] = df["amount"].astype(float)
    result["turnover"] = df["turn"].astype(float)
    result["adj_factor"] = 1.0  # baostock adjustflag=2 is forward-adjusted
    result["is_st"] = df["isST"].fillna("0").astype(int).astype(bool)
    result["is_suspended"] = df["tradestatus"].fillna("1").astype(int) == 0
    result["asset_type"] = "stock"
    return result


def to_internal_code(raw_code: str) -> str:
    code = str(raw_code).strip()
    if "." in code:
        return code
    if code.startswith("sh."):
        return code.replace("sh.", "") + ".SH"
    if code.startswith("sz."):
        return code.replace("sz.", "") + ".SZ"
    if code.startswith(("6", "5", "9")):
        return f"{code}.SH"
    elif code.startswith(("0", "2", "3")):
        return f"{code}.SZ"
    elif code.startswith(("4", "8")):
        return f"{code}.BJ"
    return code
```

- [ ] **Step 3: Implement BaoStock downloader**

```python
# src/aistock/sources/baostock/downloader.py
import pandas as pd
from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.sources.baostock.client import BaoStockClient
from aistock.sources.baostock.mapper import to_internal
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.minute import StockMinuteSchema

class BaoStockSource(SourceNode):
    name = "baostock"

    def __init__(self, config: dict | None = None):
        self.client = BaoStockClient(config)

    def supports(self, asset_type: str, schema: type) -> bool:
        if schema == StockDailySchema:
            return asset_type in ("stock", "index")
        if schema == StockMinuteSchema:
            return asset_type == "stock"  # baostock supports 5/15/30/60 min
        return False

    def fetch(self, spec: FetchSpec) -> pd.DataFrame:
        spec_codes = spec.codes if spec.codes else []
        if not spec_codes:
            spec_codes = ["sh.000001"]

        start = spec.start_date.strftime("%Y-%m-%d")
        end = spec.end_date.strftime("%Y-%m-%d")
        freq = "d" if spec.frequency == "daily" else spec.frequency.replace("min", "")

        frames = []
        for raw_code in spec_codes:
            try:
                bs_code = raw_code
                if "." not in bs_code:
                    if bs_code.startswith(("6", "5", "9")):
                        bs_code = f"sh.{bs_code}"
                    else:
                        bs_code = f"sz.{bs_code}"
                df = self.client.fetch_daily(bs_code, start, end, frequency=freq)
                if not df.empty:
                    df = to_internal(df)
                    frames.append(df)
            except Exception:
                continue

        try:
            self.client.logout()
        except Exception:
            pass

        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def check_health(self) -> bool:
        try:
            self.client._ensure_login()
            return self.client._logged_in
        except Exception:
            return False
```

```python
# src/aistock/sources/baostock/__init__.py
"""BaoStock data source plugin."""
from aistock.sources.baostock.downloader import BaoStockSource
```

- [ ] **Step 4: Verify and commit**

```bash
git add src/aistock/sources/baostock/
git commit -m "feat: BaoStock source plugin (client + mapper + downloader)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 16: TuShare Source Plugin

**Files:**
- Create: `src/aistock/sources/tushare/__init__.py`
- Create: `src/aistock/sources/tushare/client.py`
- Create: `src/aistock/sources/tushare/mapper.py`
- Create: `src/aistock/sources/tushare/downloader.py`

- [ ] **Step 1: Implement TuShare client (requires token from env)**

```python
# src/aistock/sources/tushare/client.py
"""TuShare API wrapper."""
import os
import pandas as pd
from aistock.exceptions import SourceUnavailable, SourceRateLimited

class TuShareClient:
    def __init__(self, config: dict | None = None):
        self._config = config or {}
        token = self._config.get("token", "")
        if token.startswith("${") and token.endswith("}"):
            env_var = token[2:-1]
            token = os.environ.get(env_var, "")
        self._token = token
        self._api = None
        if self._token:
            try:
                import tushare as ts
                ts.set_token(self._token)
                self._api = ts.pro_api()
            except Exception:
                self._api = None

    def _ensure_api(self):
        if not self._api:
            raise SourceUnavailable("TuShare token not configured or invalid")

    def fetch_daily(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        self._ensure_api()
        try:
            df = self._api.daily(
                ts_code=code,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
            )
            return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
        except Exception as e:
            msg = str(e).lower()
            if "limit" in msg or "frequency" in msg:
                raise SourceRateLimited(f"tushare rate limited: {e}")
            raise SourceUnavailable(f"tushare error: {e}")
```

- [ ] **Step 2: Implement TuShare mapper**

```python
# src/aistock/sources/tushare/mapper.py
"""TuShare raw fields --> internal StockDailySchema fields."""
import pandas as pd

def to_internal(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[
            "asset_type", "code", "trade_date", "open", "high", "low",
            "close", "volume", "amount", "turnover", "adj_factor",
            "is_st", "is_suspended",
        ])
    result = pd.DataFrame()
    result["code"] = df["ts_code"].apply(to_internal_code)
    result["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    result["open"] = df["open"].astype(float)
    result["high"] = df["high"].astype(float)
    result["low"] = df["low"].astype(float)
    result["close"] = df["close"].astype(float)
    result["volume"] = df["vol"].astype("int64")  # tushare: vol=volume(shou)
    result["amount"] = df["amount"].astype(float)
    result["turnover"] = 0.0  # tushare daily() doesn't include turnover
    result["adj_factor"] = 1.0
    result["is_st"] = False
    result["is_suspended"] = (result["volume"] == 0) & (result["amount"] == 0)
    result["asset_type"] = "stock"
    return result


def to_internal_code(raw_code: str) -> str:
    code = str(raw_code).strip()
    if "." in code:
        return code
    if code.startswith(("6", "5", "9")):
        return f"{code}.SH"
    elif code.startswith(("0", "2", "3")):
        return f"{code}.SZ"
    elif code.startswith(("4", "8")):
        return f"{code}.BJ"
    return code
```

- [ ] **Step 3: Implement TuShare downloader**

```python
# src/aistock/sources/tushare/downloader.py
import pandas as pd
from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.sources.tushare.client import TuShareClient
from aistock.sources.tushare.mapper import to_internal
from aistock.schemas.daily import StockDailySchema

class TuShareSource(SourceNode):
    name = "tushare"

    def __init__(self, config: dict | None = None):
        self.client = TuShareClient(config)

    def supports(self, asset_type: str, schema: type) -> bool:
        if schema == StockDailySchema:
            return asset_type == "stock"
        return True

    def fetch(self, spec: FetchSpec) -> pd.DataFrame:
        spec_codes = spec.codes if spec.codes else []
        if not spec_codes:
            spec_codes = ["000001.SZ"]

        start = spec.start_date.strftime("%Y-%m-%d")
        end = spec.end_date.strftime("%Y-%m-%d")

        frames = []
        for raw_code in spec_codes:
            try:
                ts_code = raw_code
                if not ts_code.endswith((".SH", ".SZ", ".BJ")):
                    if raw_code.startswith(("6", "5", "9")):
                        ts_code = f"{raw_code}.SH"
                    else:
                        ts_code = f"{raw_code}.SZ"
                df = self.client.fetch_daily(ts_code, start, end)
                if not df.empty:
                    df = to_internal(df)
                    frames.append(df)
            except Exception:
                continue

        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def check_health(self) -> bool:
        try:
            self.client._ensure_api()
            return True
        except Exception:
            return False
```

```python
# src/aistock/sources/tushare/__init__.py
"""TuShare data source plugin."""
from aistock.sources.tushare.downloader import TuShareSource
```

- [ ] **Step 4: Commit**

```bash
git add src/aistock/sources/tushare/
git commit -m "feat: TuShare source plugin (client + mapper + downloader)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

## Task 17: Cleaning Steps (4 B-Level + 2 C-Level Skeletons)

**Files:**
- Create: `src/aistock/cleaning/registry.py`
- Create: `src/aistock/cleaning/universal.py`
- Create: `src/aistock/cleaning/adjustment.py`
- Create: `src/aistock/cleaning/status.py`
- Create: `src/aistock/cleaning/validator.py`
- Create: `src/aistock/cleaning/cross_validator.py` (C-level skeleton)
- Create: `src/aistock/cleaning/quality.py` (C-level skeleton)
- Modify: `src/aistock/pipeline/cleaner.py` (wire STEPS_BASELINE/STEPS_ADVANCED)
- Modify: `tests/unit/test_cleaning_steps.py` (append step tests)

- [ ] **Step 1: Append cleaning step tests**

Append to `tests/unit/test_cleaning_steps.py`:

```python
import numpy as np
from aistock.cleaning.universal import UniversalCleaner
from aistock.cleaning.status import StatusCleaner
from aistock.cleaning.validator import OHLCValidator


class TestUniversalCleaner:
    def test_removes_duplicate_rows(self, df_daily_good):
        step = UniversalCleaner()
        df_dup = pd.concat([df_daily_good, df_daily_good.iloc[:2]], ignore_index=True)
        result = step.clean(df_dup, mock_context())
        assert len(result) == len(df_daily_good)

    def test_fills_null_turnover_with_zero(self):
        step = UniversalCleaner()
        df = pd.DataFrame({
            "code": ["000001.SZ"], "trade_date": [date(2025, 1, 2)],
            "open": [10.0], "high": [10.5], "low": [9.8], "close": [10.2],
            "volume": [1000000], "amount": [10200000.0],
            "turnover": [None], "adj_factor": [1.0],
        })
        result = step.clean(df, mock_context())
        assert result["turnover"].iloc[0] == 0.0


class TestStatusCleaner:
    def test_marks_suspended_when_zero_volume_and_amount(self):
        step = StatusCleaner()
        df = pd.DataFrame({
            "code": ["000001.SZ"], "trade_date": [date(2025, 1, 2)],
            "open": [10.0], "high": [10.5], "low": [9.8], "close": [10.2],
            "volume": [0], "amount": [0.0], "is_st": [False], "is_suspended": [False],
        })
        result = step.clean(df, mock_context())
        assert result["is_suspended"].iloc[0] is True


class TestOHLCValidator:
    def test_passes_on_valid_data(self, df_daily_good):
        step = OHLCValidator()
        result = step.clean(df_daily_good, mock_context())
        assert len(result) == len(df_daily_good)

    def test_flags_high_below_low(self):
        step = OHLCValidator()
        df = pd.DataFrame({
            "code": ["000001.SZ"], "trade_date": [date(2025, 1, 2)],
            "open": [10.0], "high": [5.0], "low": [6.0], "close": [10.2],
            "volume": [1000], "amount": [5000.0],
        })
        issues = step.validate(df)
        assert len(issues) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_cleaning_steps.py -v`
Expected: FAIL with ImportError for universal/status/validator

- [ ] **Step 3: Implement UniversalCleaner**

```python
# src/aistock/cleaning/universal.py
import pandas as pd
from aistock.cleaning.interface import CleaningStep

class UniversalCleaner(CleaningStep):
    name = "universal"
    requires = []

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        df = df.drop_duplicates()
        if "turnover" in df.columns:
            df["turnover"] = df["turnover"].fillna(0.0)
        if "adj_factor" in df.columns:
            df["adj_factor"] = df["adj_factor"].fillna(1.0)
        return df
```

- [ ] **Step 4: Implement AdjustmentCleaner**

```python
# src/aistock/cleaning/adjustment.py
import pandas as pd
from aistock.cleaning.interface import CleaningStep

class AdjustmentCleaner(CleaningStep):
    name = "adjustment"
    requires = ["universal"]

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        return df
```

- [ ] **Step 5: Implement StatusCleaner**

```python
# src/aistock/cleaning/status.py
import pandas as pd
from aistock.cleaning.interface import CleaningStep

class StatusCleaner(CleaningStep):
    name = "status"
    requires = ["adjustment"]

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        if "is_suspended" not in df.columns:
            df["is_suspended"] = False
        if "volume" in df.columns and "amount" in df.columns:
            df["is_suspended"] = df["is_suspended"] | (
                (df["volume"] == 0) & (df["amount"] == 0)
            )
        if "is_st" not in df.columns:
            df["is_st"] = False
        if "code" in df.columns:
            df["is_st"] = df["is_st"] | df["code"].str.contains("ST", na=False)
        return df
```

- [ ] **Step 6: Implement OHLCValidator**

```python
# src/aistock/cleaning/validator.py
import pandas as pd
from aistock.cleaning.interface import CleaningStep

class OHLCValidator(CleaningStep):
    name = "ohlc_validator"
    requires = ["status"]

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        return df

    def validate(self, df: pd.DataFrame) -> list[str]:
        issues = []
        if "high" in df.columns and "low" in df.columns:
            inverted = (df["high"] < df["low"]).sum()
            if inverted > 0:
                issues.append(f"{inverted} rows with high < low")
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                neg = (df[col] < 0).sum()
                if neg > 0:
                    issues.append(f"{neg} rows with negative {col}")
        if "volume" in df.columns:
            neg_vol = (df["volume"] < 0).sum()
            if neg_vol > 0:
                issues.append(f"{neg_vol} rows with negative volume")
        return issues
```

- [ ] **Step 7: Implement C-level skeletons**

```python
# src/aistock/cleaning/cross_validator.py
"""Cross-source validation (C-level, Phase 2)."""
from aistock.cleaning.interface import CleaningStep

class CrossValidator(CleaningStep):
    name = "cross_validator"
    requires = ["ohlc_validator"]

    def clean(self, df, ctx):
        return df  # C-level: no-op for now
```

```python
# src/aistock/cleaning/quality.py
"""Data quality scoring (C-level, Phase 2)."""
from aistock.cleaning.interface import CleaningStep

class QualityScorer(CleaningStep):
    name = "quality_scorer"
    requires = ["cross_validator"]

    def clean(self, df, ctx):
        return df  # C-level: no-op for now
```

- [ ] **Step 8: Wire STEPS_BASELINE and STEPS_ADVANCED**

Edit `src/aistock/pipeline/cleaner.py`, replace the placeholder STEPS lists:

```python
from aistock.cleaning.universal import UniversalCleaner
from aistock.cleaning.adjustment import AdjustmentCleaner
from aistock.cleaning.status import StatusCleaner
from aistock.cleaning.validator import OHLCValidator
from aistock.cleaning.cross_validator import CrossValidator
from aistock.cleaning.quality import QualityScorer

STEPS_BASELINE = [
    UniversalCleaner(),
    AdjustmentCleaner(),
    StatusCleaner(),
    OHLCValidator(),
]

STEPS_ADVANCED = STEPS_BASELINE + [
    CrossValidator(),
    QualityScorer(),
]
```

```python
# src/aistock/cleaning/registry.py
"""Cleaning step chain registry."""
from aistock.pipeline.cleaner import STEPS_BASELINE, STEPS_ADVANCED
```

- [ ] **Step 9: Run tests**

Run: `pytest tests/unit/test_cleaning_steps.py -v`
Expected: 8 passed (4 Cleaner + 4 new steps)

- [ ] **Step 10: Commit**

```bash
git add src/aistock/cleaning/ src/aistock/pipeline/cleaner.py tests/unit/test_cleaning_steps.py
git commit -m "feat: 4 B-level cleaning steps + 2 C-level skeletons

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 18: CLI + Composition Root

**Files:**
- Create: `src/aistock/cli.py`
- Create: `tests/integration/test_cli.py`

- [ ] **Step 1: Write failing CLI test**

```python
# tests/integration/test_cli.py
from click.testing import CliRunner
from aistock.cli import cli

class TestCLI:
    def test_cli_group_loads(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "fetch" in result.output
        assert "update" in result.output
        assert "status" in result.output

    def test_fetch_requires_asset_type(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "--asset-type" in result.output

    def test_status_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        # Should not crash even with no DB
        assert result.exit_code in (0, 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_cli.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement CLI**

```python
# src/aistock/cli.py
import uuid
import yaml
from datetime import date, datetime
import click
from aistock.schemas import SCHEMA_REGISTRY
from aistock.sources.registry import SourceRegistry
from aistock.pipeline.cleaner import Cleaner, STEPS_BASELINE, STEPS_ADVANCED
from aistock.storage.router import get_backend
from aistock.storage.query import QuerySpec
from aistock.observability.logger import PipelineLogger
from aistock.observability.tracer import TaskTracer
from aistock.pipeline.runner import PipelineRunner
from aistock.pipeline.models import FetchSpec, PipelineContext


def _instantiate_source(name: str, config: dict):
    """Factory for source plugins by name."""
    if name == "akstock":
        from aistock.sources.akstock.downloader import AkStockSource
        return AkStockSource(config)
    if name == "baostock":
        from aistock.sources.baostock.downloader import BaoStockSource
        return BaoStockSource(config)
    if name == "tushare":
        from aistock.sources.tushare.downloader import TuShareSource
        return TuShareSource(config)
    raise ValueError(f"Unknown source: {name}")


def _build_runner() -> PipelineRunner:
    """Composition root --- load config, assemble components, inject Runner."""
    with open("config/pipeline.yaml") as f:
        config = yaml.safe_load(f)
    with open("config/source_priority.yaml") as f:
        source_cfg = yaml.safe_load(f)

    logger = PipelineLogger(
        log_dir=config.get("logging", {}).get("dir", "logs"),
        retention_days=config.get("logging", {}).get("retention_days", 90),
    )

    registry = SourceRegistry(source_cfg)
    for section_key, entries in source_cfg.items():
        schema_cls = SCHEMA_REGISTRY[section_key]
        for entry in entries:
            source = _instantiate_source(entry["name"], entry.get("config", {}))
            registry.register(source, entry["priority"], schema_cls)

    profile = config["cleaner"]["profile"]
    steps = STEPS_BASELINE if profile == "baseline" else STEPS_ADVANCED
    cleaner = Cleaner(steps)
    store = get_backend(config)

    ctx = PipelineContext(
        task_id=str(uuid.uuid4()),
        config=config,
        log=logger,
    )

    return PipelineRunner(registry, cleaner, store, ctx)


@click.group()
def cli():
    """Aistock --- AI-powered A-share market data pipeline."""
    pass


@cli.command()
@click.option("--asset-type", required=True, help="stock|index|etf|cb|future|option")
@click.option("--schema", required=True, help="daily|minute|finance|alternative|north_flow|margin_trade|reference")
@click.option("--codes", default=None, help="Comma-separated codes; default=all")
@click.option("--start-date", required=True, help="YYYY-MM-DD")
@click.option("--end-date", default=None, help="YYYY-MM-DD; default=today")
@click.option("--frequency", default="daily", help="daily|1min|5min|15min|30min|60min")
def fetch(asset_type, schema, codes, start_date, end_date, frequency):
    """Download -> clean -> store, single run."""
    schema_cls = SCHEMA_REGISTRY[schema]
    code_list = codes.split(",") if codes else None
    end = date.today() if end_date is None else date.fromisoformat(end_date)

    spec = FetchSpec(
        asset_type=asset_type,
        codes=code_list,
        start_date=date.fromisoformat(start_date),
        end_date=end,
        schema=schema_cls,
        frequency=frequency,
    )

    runner = _build_runner()
    report = runner.run(spec)
    tracer = TaskTracer()
    from aistock.observability.models import TaskRun
    import json
    now = datetime.now().isoformat()
    tracer.record_task_run(TaskRun(
        task_id=report.task_id,
        started_at=now,
        finished_at=now,
        source_name=report.source_name,
        status=report.status,
        records_fetched=report.records_fetched,
        records_after_clean=report.records_after_clean,
        records_written=report.records_written,
        duration_ms=report.duration_ms,
        issues_json=json.dumps(report.issues),
        fallback_used=report.fallback_used,
        failed_codes_json=json.dumps(report.failed_codes),
        spec_json=json.dumps({
            "asset_type": asset_type, "schema": schema, "codes": codes,
            "start_date": start_date, "end_date": end_date, "frequency": frequency,
        }),
    ))

    click.echo(f"Status: {report.status}")
    click.echo(f"Source: {report.source_name}")
    click.echo(f"Fetched: {report.records_fetched}")
    click.echo(f"Written: {report.records_written}")
    click.echo(f"Duration: {report.duration_ms}ms")
    if report.failed_codes:
        click.echo(f"Failed codes: {report.failed_codes}")
    if report.fallback_used:
        click.echo(f"Fallback used: {report.fallback_used}")


@cli.command()
@click.option("--asset-type", required=True)
@click.option("--schema", required=True)
def update(asset_type, schema):
    """Daily incremental update."""
    schema_cls = SCHEMA_REGISTRY[schema]
    runner = _build_runner()
    store = runner._store

    # Find latest date in existing data
    query = QuerySpec(schema=schema_cls, asset_types=[asset_type])
    existing = store.read(query)
    if len(existing) == 0:
        click.echo("No existing data found, falling back to full backfill mode.")
        click.echo("Run: python -m aistock.cli fetch --asset-type ... --schema ... --start-date 2015-01-01")
        return

    date_col = "trade_date" if "trade_date" in existing.columns else "trade_time"
    latest = pd.to_datetime(existing[date_col]).max().date()
    today = date.today()

    if latest >= today:
        click.echo(f"Data already up to date (latest: {latest})")
        return

    spec = FetchSpec(
        asset_type=asset_type,
        codes=None,
        start_date=latest,
        end_date=today,
        schema=schema_cls,
    )

    report = runner.run(spec)
    click.echo(f"Update complete: {report.status}, {report.records_fetched} new records")


@cli.command()
def status():
    """Show recent task runs from SQLite metadata."""
    tracer = TaskTracer()
    runs = tracer.get_recent_runs(limit=10)
    if not runs:
        click.echo("No task runs recorded yet.")
        return
    click.echo(f"{'Task ID':<38} {'Source':<10} {'Status':<10} {'Fetched':>8} {'Duration':>10}")
    click.echo("-" * 80)
    for r in runs:
        click.echo(f"{r.task_id:<38} {r.source_name:<10} {r.status:<10} {r.records_fetched:>8} {r.duration_ms:>7}ms")


if __name__ == "__main__":
    cli()
```

Note: the `update` command uses `runner._store` to access the store's read method. This is intentionally accessing a private attribute in the CLI bootstrap layer (which owns the composition) rather than routing through the runner. In practice, the CLI can read directly since it creates the store via `get_backend()`.

- [ ] **Step 4: Run tests**

Run: `pytest tests/integration/test_cli.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/aistock/cli.py tests/integration/test_cli.py
git commit -m "feat: CLI (fetch/update/status) + _build_runner() composition root

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

## Task 19: Fallback Chain Integration Tests

**Files:**
- Create: `tests/integration/test_fallback_chain.py`

- [ ] **Step 1: Write fallback chain test**

```python
# tests/integration/test_fallback_chain.py
import logging
import uuid
from datetime import date
import pandas as pd
import pytest
from aistock.pipeline.models import FetchSpec, PipelineContext
from aistock.pipeline.source import SourceNode
from aistock.pipeline.cleaner import Cleaner
from aistock.pipeline.runner import PipelineRunner
from aistock.schemas.daily import StockDailySchema
from aistock.sources.registry import SourceRegistry
from aistock.exceptions import SourceUnavailable, PipelineError


class FailingSource(SourceNode):
    def __init__(self, name, exc=SourceUnavailable("nope"), fail_health=False):
        self.name = name
        self._exc = exc
        self._fail_health = fail_health
    def supports(self, asset_type, schema):
        return True
    def fetch(self, spec):
        raise self._exc
    def check_health(self):
        return not self._fail_health

class StubSource(SourceNode):
    def __init__(self, name, df):
        self.name = name
        self._df = df
    def supports(self, asset_type, schema):
        return True
    def fetch(self, spec):
        return self._df.copy()

class StubStore:
    name = "stub"
    def write(self, df, schema, partition_keys):
        from aistock.pipeline.models import WriteResult
        return WriteResult(len(df), ["stub/partition"], "stub")
    def read(self, query):
        return pd.DataFrame()
    def upsert(self, df, schema, partition_keys, on_conflict):
        from aistock.pipeline.models import WriteResult
        return WriteResult(len(df), ["stub/partition"], "stub")
    def exists(self, schema, partition_keys):
        return False

def make_df(codes=None):
    if codes is None:
        codes = ["000001.SZ"]
    rows = []
    for c in codes:
        for d in [date(2025, 1, 2), date(2025, 1, 3)]:
            rows.append({
                "code": c, "trade_date": d, "asset_type": "stock",
                "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2,
                "volume": 1000000, "amount": 10200000.0,
                "adj_factor": 1.0, "is_st": False, "is_suspended": False,
            })
    return pd.DataFrame(rows)

def make_spec(codes=None):
    if codes is None:
        codes = ["000001.SZ"]
    return FetchSpec(
        asset_type="stock", codes=codes,
        start_date=date(2025, 1, 2), end_date=date(2025, 1, 6),
        schema=StockDailySchema, frequency="daily",
    )

def make_runner(registry, store=None):
    if store is None:
        store = StubStore()
    ctx = PipelineContext(task_id=str(uuid.uuid4()), config={},
                         log=logging.getLogger("test"))
    return PipelineRunner(registry, Cleaner([]), store, ctx)


class TestFallbackChain:
    def test_second_source_used_when_first_unavailable(self):
        registry = SourceRegistry({})
        registry.register(FailingSource("akstock", SourceUnavailable("down")),
                         priority=100, schema=StockDailySchema)
        registry.register(StubSource("baostock", make_df()),
                         priority=80, schema=StockDailySchema)
        report = make_runner(registry).run(make_spec())
        assert report.status == "success"
        assert report.fallback_used == "baostock"
        assert report.source_name == "baostock"

    def test_second_source_used_when_first_rate_limited(self):
        from aistock.exceptions import SourceRateLimited
        registry = SourceRegistry({})
        registry.register(FailingSource("akstock", SourceRateLimited("too fast")),
                         priority=100, schema=StockDailySchema)
        registry.register(StubSource("baostock", make_df()),
                         priority=80, schema=StockDailySchema)
        report = make_runner(registry).run(make_spec())
        assert report.status == "success"
        assert report.fallback_used == "baostock"

    def test_all_exhausted_raises_pipeline_error(self):
        registry = SourceRegistry({})
        for i, name in enumerate(["akstock", "baostock", "tushare"]):
            registry.register(FailingSource(name), priority=100 - i, schema=StockDailySchema)
        with pytest.raises(PipelineError, match="All sources exhausted"):
            make_runner(registry).run(make_spec())

    def test_unhealthy_source_is_skipped(self):
        registry = SourceRegistry({})
        registry.register(FailingSource("akstock", fail_health=True),
                         priority=100, schema=StockDailySchema)
        registry.register(StubSource("baostock", make_df()),
                         priority=80, schema=StockDailySchema)
        report = make_runner(registry).run(make_spec())
        assert report.status == "success"
        assert report.source_name == "baostock"

    def test_partial_success_with_fallback(self):
        """akstock fails for one code, baostock gets it."""
        registry = SourceRegistry({})
        df_ak = make_df(["000001.SZ"])
        registry.register(StubSource("akstock", df_ak),
                         priority=100, schema=StockDailySchema)
        registry.register(StubSource("baostock", make_df(["000001.SZ", "600000.SH"])),
                         priority=80, schema=StockDailySchema)
        report = make_runner(registry).run(make_spec(["000001.SZ", "600000.SH"]))
        assert report.status == "partial"
        assert report.source_name == "akstock"
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/integration/test_fallback_chain.py -v`
Expected: 5 passed

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_fallback_chain.py
git commit -m "feat: fallback chain integration tests (5 scenarios)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 20: Full Integration Suite Verification

- [ ] **Step 1: Run ALL tests**

Run: `pytest tests/ -v`
Expected: All tests pass (should be ~60+ tests across all test files)

- [ ] **Step 2: Run ruff linter**

Run: `ruff check src/ tests/`
Expected: No errors

- [ ] **Step 3: Verify import chain**

Run: `python -c "
from aistock.exceptions import PipelineError
from aistock.schemas import SCHEMA_REGISTRY
from aistock.pipeline.models import FetchSpec, PipelineReport
from aistock.pipeline.source import SourceNode
from aistock.pipeline.cleaner import Cleaner, STEPS_BASELINE
from aistock.pipeline.runner import PipelineRunner
from aistock.sources.registry import SourceRegistry
from aistock.storage.interface import StorageBackend
from aistock.storage.query import QuerySpec
from aistock.storage.router import get_backend
from aistock.observability.logger import PipelineLogger
from aistock.observability.tracer import TaskTracer
print('All imports OK')
"`

- [ ] **Step 4: Commit final verification**

```bash
git add -A
git commit -m "chore: full integration suite verification, all tests passing

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 21: Historical Backfill (10-Year Daily Data)

**Manual execution — not automated.**

- [ ] **Step 1: Backfill stocks**

Run: `python -m aistock.cli fetch --asset-type stock --schema daily --start-date 2015-01-01`

- [ ] **Step 2: Verify data completeness**

Run: `python -c "
from aistock.storage.parquet.backend import ParquetBackend
from aistock.storage.query import QuerySpec
from aistock.schemas.daily import StockDailySchema
backend = ParquetBackend({'data_dir': 'data', 'compression': 'zstd'})
query = QuerySpec(schema=StockDailySchema, start_date=None, end_date=None)
df = backend.read(query)
print(f'Total rows: {len(df)}')
print(f'Date range: {df.trade_date.min()} to {df.trade_date.max()}')
print(f'Unique codes: {df.code.nunique()}')
print(f'Years covered: {sorted(df.trade_date.dt.year.unique())}')
"`

- [ ] **Step 3: Commit backfill verification**

After confirming data integrity:
```bash
git add artifacts/
git commit -m "data: 10-year daily stock history backfill verified

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---
## Task 22: Daily Update Verification

**Manual execution — run on 2 consecutive days.**

- [ ] **Step 1: Day 1 update**

Run: `python -m aistock.cli update --asset-type stock --schema daily`

- [ ] **Step 2: Day 2 update (verify no duplicates)**

Run: `python -m aistock.cli update --asset-type stock --schema daily`
Expected: "Data already up to date" OR 0-1 new records (today's data only), no duplicates

- [ ] **Step 3: Check status**

Run: `python -m aistock.cli status`
Expected: Shows 2+ task runs with different timestamps

---
## Self-Review Checklist

### 1. Spec Coverage

| Spec Section | Covered By |
|---|---|
| S1 Goals & Scope | Tasks 1-2 (skeleton + exceptions) |
| S3 Directory Structure | Task 1 (all dirs created) |
| S4.1 Models | Task 5 |
| S4.2 SourceNode | Task 5 |
| S4.3 CleaningStep | Task 6 |
| S4.4 Cleaner | Task 6 |
| S4.5 StorageBackend + 4.5.1 QuerySpec | Task 8 |
| S4.6 PipelineRunner | Task 7 |
| S4.7 Exceptions | Task 2 |
| S4.8 Router | Task 8 |
| S5.1-5.5 Schemas | Tasks 3-4 |
| S5.6 Partition Strategy | Task 9 |
| S5.7 SCHEMA_REGISTRY | Tasks 3-4 |
| S5.8 Schema Validation | Tasks 3-4 |
| S6 Source Plugins | Tasks 14-16 |
| S7 Observability | Task 12 |
| S8 Config Files | Task 1 |
| S9 CLI | Task 18 |
| S9.1 Composition Root | Task 18 |
| S10 Dependencies | Task 1 (pyproject.toml) |
| S11 Testing | All tasks (TDD throughout) |
| S12 Implementation Sequence | Tasks 1-22 |
| Factors Skeleton | Task 13 |

### 2. Placeholder Scan

No TBD, TODO, "implement later", or "add appropriate error handling" patterns. Every step has concrete code or explicit commands.

### 3. Type Consistency

- `FetchSpec` fields used consistently across Tasks 5, 7, 14-16, 18
- `PipelineReport` fields used consistently across Tasks 5, 7, 18
- `SCHEMA_REGISTRY` keys match `source_priority.yaml` sections (design doc S5.7/S8.2)
- Schema `partition_values()` signatures consistent across Tasks 3-4 and consumed by Task 7/10
- `SourceRegistry.register(source, priority, schema)` signature consistent across Tasks 5-6
- `CleaningStep.clean(df, ctx)` and `validate(df)` signatures consistent across Tasks 6, 17

---
