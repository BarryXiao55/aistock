"""PipelineRunner --- full pipeline orchestration with fallback."""

import time

import pandas as pd

from aistock.exceptions import (
    CleanError,
    PipelineError,
    SourceRateLimited,
    SourceUnavailable,
    StoreError,
)
from aistock.pipeline.cleaner import Cleaner
from aistock.pipeline.models import PipelineReport
from aistock.pipeline.source import SourceNode
from aistock.sources.registry import SourceRegistry
from aistock.storage.interface import StorageBackend


class PipelineRunner:
    """执行一次管道任务，负责 Source->Clean->Store 全链路编排 + 降级"""

    def __init__(
        self,
        registry: SourceRegistry,
        cleaner: Cleaner,
        store: StorageBackend,
        ctx,
    ):
        self._registry = registry
        self._cleaner = cleaner
        self._store = store
        self._ctx = ctx

    def run(self, spec) -> PipelineReport:
        """执行管道任务"""
        issues_overall = []
        start_time = time.monotonic()

        for source in self._registry.get_all(spec.asset_type, spec.schema):
            try:
                if not source.check_health():
                    self._ctx.log.info(f"source [{source.name}] unhealthy, skipping")
                    continue

                # 1. Fetch
                df = source.fetch_with_retry(spec)
                records_fetched = len(df)

                # 2. Schema 边界校验
                schema_issues = spec.schema.validate(df)
                if schema_issues:
                    self._ctx.log.warning(f"schema validation: {schema_issues}")
                    issues_overall.extend(schema_issues)
                    before = len(df)
                    df = df[~self._find_invalid_rows_mask(df, spec.schema)]
                    self._ctx.log.info(f"filtered {before - len(df)} invalid rows")

                # 3. Clean
                df, clean_issues = self._cleaner.clean(df, self._ctx)
                issues_overall.extend(clean_issues)

                # 4. Write
                result = self._store.write(df, spec.schema, spec.schema.partition_values(df))

                # 5. 判断成功/部分成功
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
                    fallback_used=(
                        source.name if source.name != self._registry.primary else None
                    ),
                )

            except (SourceUnavailable, SourceRateLimited, CleanError) as e:
                self._ctx.log.warning(f"source [{source.name}] failed: {e}, falling back")
                continue
            except StoreError:
                raise  # 存储层失败不降级，直接抛

        raise PipelineError("All sources exhausted --- unable to fetch data")

    @staticmethod
    def _find_invalid_rows_mask(df: pd.DataFrame, schema: type) -> pd.Series:
        """定位脏行的布尔 mask"""
        result = pd.Series(False, index=df.index)
        required = {"code", "trade_date", "open", "high", "low", "close", "volume", "amount"}
        missing = required - set(df.columns)
        if missing:
            return result
        result |= df["high"] < df["low"]
        result |= (df[["open", "high", "low", "close"]] < 0).any(axis=1)
        result |= df["volume"] < 0
        return result
