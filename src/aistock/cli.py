"""Aistock CLI --- Click-based command line interface."""

import logging
import sys
import uuid
from datetime import date, datetime

import click
import yaml

from aistock.observability.tracer import TaskTracer
from aistock.pipeline.cleaner import Cleaner, STEPS_BASELINE, STEPS_ADVANCED
from aistock.pipeline.models import FetchSpec, PipelineContext
from aistock.pipeline.runner import PipelineRunner
from aistock.schemas import SCHEMA_REGISTRY
from aistock.sources.registry import SourceRegistry
from aistock.storage.router import get_backend
from aistock.observability.adapter import LoggerAdapter


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def load_config(config_path: str = "config/pipeline.yaml") -> dict:
    """加载配置文件"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)


def load_source_config(config_path: str = "config/source_priority.yaml") -> dict:
    """加载数据源优先级配置"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        click.echo(f"Source config not found: {config_path}", err=True)
        sys.exit(1)


def _instantiate_source(source_name: str, config: dict):
    """实例化数据源"""
    if source_name == "akstock":
        from aistock.sources.akstock.downloader import AkStockSource
        return AkStockSource(config)
    elif source_name == "baostock":
        from aistock.sources.baostock.downloader import BaoStockSource
        return BaoStockSource(config)
    elif source_name == "tushare":
        from aistock.sources.tushare.downloader import TuShareSource
        return TuShareSource(config)
    else:
        raise ValueError(f"Unknown source: {source_name}")


def _build_runner(config: dict, source_cfg: dict) -> PipelineRunner:
    """组合根：加载配置 -> 组装组件 -> 注入 Runner"""
    from aistock.observability.logger import PipelineLogger

    # 1. 初始化 Logger
    log_config = config.get("logging", {})
    logger = PipelineLogger(
        log_dir=log_config.get("dir", "logs"),
        retention_days=log_config.get("retention_days", 90),
    )

    # 2. 构建 SourceRegistry
    registry = SourceRegistry(source_cfg)
    for section_key, entries in source_cfg.items():
        if section_key not in SCHEMA_REGISTRY:
            continue
        schema_cls = SCHEMA_REGISTRY[section_key]
        for entry in entries:
            source = _instantiate_source(entry["name"], entry.get("config", {}))
            registry.register(source, entry["priority"], schema_cls)

    # 3. 选择清洗链
    cleaner_profile = config.get("cleaner", {}).get("profile", "baseline")
    steps = STEPS_BASELINE if cleaner_profile == "baseline" else STEPS_ADVANCED
    cleaner = Cleaner(steps)

    # 4. 获取存储后端
    store = get_backend(config)

    # 5. 创建上下文
    task_id = str(uuid.uuid4())
    log_adapter = LoggerAdapter(logger, task_id)
    ctx = PipelineContext(
        task_id=task_id,
        config=config,
        log=log_adapter,
    )

    return PipelineRunner(registry, cleaner, store, ctx)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Aistock --- AI-powered A-share market data pipeline."""
    setup_logging()


@cli.command()
@click.option("--asset-type", required=True, help="Asset type: stock, index, etf")
@click.option("--schema", "schema_name", required=True, help="Schema: daily, minute, finance")
@click.option("--codes", default=None, help="Comma-separated codes, default: all")
@click.option("--start-date", required=True, help="Start date: YYYY-MM-DD")
@click.option("--end-date", default=None, help="End date: YYYY-MM-DD, default: today")
@click.option("--frequency", default="daily", help="Frequency: daily, 1min, 5min")
def fetch(asset_type, schema_name, codes, start_date, end_date, frequency):
    """Download data -> clean -> store (single run)"""
    config = load_config()
    source_cfg = load_source_config()

    # 解析参数
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()
    code_list = codes.split(",") if codes else None

    # 获取 Schema 类
    if schema_name not in SCHEMA_REGISTRY:
        click.echo(f"Unknown schema: {schema_name}", err=True)
        sys.exit(1)
    schema_cls = SCHEMA_REGISTRY[schema_name]

    # 构建 Runner
    runner = _build_runner(config, source_cfg)

    # 初始化 Tracer
    tracer = TaskTracer()

    # 构建 FetchSpec
    spec = FetchSpec(
        asset_type=asset_type,
        codes=code_list,
        start_date=start,
        end_date=end,
        schema=schema_cls,
        frequency=frequency,
    )

    # 执行
    click.echo(f"Fetching {schema_name} data for {asset_type}...")
    click.echo(f"Date range: {start} to {end}")

    report = runner.run(spec)

    # 记录任务到 Tracer
    import json
    from aistock.observability.models import TaskRun

    task = TaskRun(
        id=report.task_id,
        started_at=datetime.now(),
        source_name=report.source_name,
        status=report.status,
        records_fetched=report.records_fetched,
        records_after_clean=report.records_after_clean,
        records_written=report.records_written,
        duration_ms=report.duration_ms,
        issues_json=json.dumps(report.issues),
        fallback_used=report.fallback_used,
        failed_codes_json=json.dumps(report.failed_codes),
    )
    task.finished_at = datetime.now()
    tracer.finish_task(task)

    # 输出结果
    click.echo("\n" + "=" * 60)
    click.echo(f"Task ID: {report.task_id}")
    click.echo(f"Source: {report.source_name}")
    click.echo(f"Status: {report.status}")
    click.echo(f"Records fetched: {report.records_fetched}")
    click.echo(f"Records after clean: {report.records_after_clean}")
    click.echo(f"Records written: {report.records_written}")
    click.echo(f"Duration: {report.duration_ms}ms")

    if report.fallback_used:
        click.echo(f"Fallback used: {report.fallback_used}")

    if report.failed_codes:
        click.echo(f"Failed codes: {', '.join(report.failed_codes)}")

    if report.issues:
        click.echo("\nIssues:")
        for issue in report.issues:
            click.echo(f"  - {issue}")

    click.echo("=" * 60)


@cli.command()
@click.option("--asset-type", required=True, help="Asset type: stock, index, etf")
@click.option("--schema", "schema_name", required=True, help="Schema: daily, minute, finance")
def update(asset_type, schema_name):
    """
    Daily update:
    1. Query latest trade_date from storage
    2. Incremental download from latest_date + 1 to today
    3. Upsert to storage
    """
    config = load_config()
    source_cfg = load_source_config()

    # 获取 Schema 类
    if schema_name not in SCHEMA_REGISTRY:
        click.echo(f"Unknown schema: {schema_name}", err=True)
        sys.exit(1)
    schema_cls = SCHEMA_REGISTRY[schema_name]

    # 构建 Runner
    runner = _build_runner(config, source_cfg)

    # 查询最新日期
    store = get_backend(config)
    from aistock.storage.query import QuerySpec

    query = QuerySpec(schema=schema_cls, partition_keys={"asset_type": asset_type})
    df = store.read(query)

    if df.empty:
        click.echo("No existing data found. Please run 'fetch' first.")
        sys.exit(1)

    # 获取最新日期
    date_col = "trade_date" if "trade_date" in df.columns else "trade_time"
    latest_date = df[date_col].max()

    # 计算增量日期范围
    if isinstance(latest_date, str):
        latest_date = datetime.strptime(latest_date, "%Y-%m-%d").date()

    start = latest_date + __import__("datetime").timedelta(days=1)
    end = date.today()

    if start > end:
        click.echo("Data is already up to date.")
        sys.exit(0)

    # 构建 FetchSpec
    spec = FetchSpec(
        asset_type=asset_type,
        codes=None,
        start_date=start,
        end_date=end,
        schema=schema_cls,
    )

    # 执行
    click.echo(f"Updating {schema_name} data for {asset_type}...")
    click.echo(f"Date range: {start} to {end}")

    report = runner.run(spec)

    # 输出结果
    click.echo("\n" + "=" * 60)
    click.echo(f"Task ID: {report.task_id}")
    click.echo(f"Status: {report.status}")
    click.echo(f"Records written: {report.records_written}")
    click.echo(f"Duration: {report.duration_ms}ms")
    click.echo("=" * 60)


@cli.command()
def status():
    """View recent task run status"""
    from aistock.observability.tracer import TaskTracer

    tracer = TaskTracer()
    tasks = tracer.get_recent_tasks(limit=10)

    if not tasks:
        click.echo("No recent tasks found.")
        return

    click.echo("\n" + "=" * 80)
    click.echo(f"{'Task ID':<40} {'Source':<15} {'Status':<10} {'Duration':<10}")
    click.echo("-" * 80)

    for task in tasks:
        click.echo(
            f"{task.id:<40} {task.source_name:<15} {task.status:<10} {task.duration_ms:<10}"
        )

    click.echo("=" * 80)


if __name__ == "__main__":
    cli()
