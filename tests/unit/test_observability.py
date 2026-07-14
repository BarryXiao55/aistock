"""Test observability modules."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from aistock.observability.logger import PipelineLogger
from aistock.observability.models import DataSnapshot, TaskRun
from aistock.observability.tracer import TaskTracer


class TestPipelineLogger:
    """测试 PipelineLogger"""

    def test_creates_log_directory(self, tmp_path):
        """测试创建日志目录"""
        log_dir = tmp_path / "test_logs"
        logger = PipelineLogger(log_dir=str(log_dir))
        assert log_dir.exists()

    def test_logs_info_message(self, tmp_path):
        """测试 INFO 级别日志"""
        logger = PipelineLogger(log_dir=str(tmp_path))
        logger.info("test_step", "Test message", task_id="test-123")

        # 验证日志文件已创建
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = tmp_path / today / "task_test-123.jsonl"
        assert log_file.exists()

        # 验证日志内容
        with open(log_file, "r") as f:
            line = f.readline()
            log_entry = json.loads(line)
            assert log_entry["level"] == "INFO"
            assert log_entry["step"] == "test_step"
            assert log_entry["message"] == "Test message"
            assert log_entry["task_id"] == "test-123"

    def test_logs_with_extra_fields(self, tmp_path):
        """测试带额外字段的日志"""
        logger = PipelineLogger(log_dir=str(tmp_path))
        logger.info(
            "fetch",
            "Fetched data",
            task_id="test-456",
            records=100,
            source="akstock",
        )

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = tmp_path / today / "task_test-456.jsonl"

        with open(log_file, "r") as f:
            line = f.readline()
            log_entry = json.loads(line)
            assert log_entry["records"] == 100
            assert log_entry["source"] == "akstock"

    def test_read_logs(self, tmp_path):
        """测试读取日志"""
        logger = PipelineLogger(log_dir=str(tmp_path))

        # 写入多条日志
        logger.info("step1", "Message 1", task_id="test-789")
        logger.warning("step2", "Message 2", task_id="test-789")

        # 读取日志
        logs = logger.read_logs("test-789")
        assert len(logs) == 2
        assert logs[0]["message"] == "Message 1"
        assert logs[1]["message"] == "Message 2"

    def test_cleanup_old_logs(self, tmp_path):
        """测试清理旧日志"""
        logger = PipelineLogger(log_dir=str(tmp_path), retention_days=0)

        # 创建旧日志目录
        old_date = "2020-01-01"
        old_dir = tmp_path / old_date
        old_dir.mkdir()
        (old_dir / "task_old.jsonl").write_text('{"test": "data"}')

        # 执行清理
        logger.cleanup()

        # 验证旧目录已删除
        assert not old_dir.exists()


class TestTaskTracer:
    """测试 TaskTracer"""

    @pytest.fixture
    def tracer(self, tmp_path):
        """创建临时追踪器"""
        db_path = tmp_path / "test.db"
        return TaskTracer(db_path=str(db_path))

    def test_init_creates_database(self, tracer):
        """测试初始化创建数据库"""
        assert tracer._db_path.exists()

    def test_start_task(self, tracer):
        """测试开始任务"""
        task = tracer.start_task("test-001", spec_json='{"test": true}')
        assert task.id == "test-001"
        assert task.status == "running"

    def test_finish_task(self, tracer):
        """测试完成任务"""
        task = tracer.start_task("test-002")
        task.source_name = "akstock"
        task.status = "success"
        task.records_fetched = 100
        task.records_after_clean = 98
        task.records_written = 98
        task.duration_ms = 1500

        tracer.finish_task(task)

        # 验证任务已完成
        retrieved = tracer.get_task("test-002")
        assert retrieved is not None
        assert retrieved.status == "success"
        assert retrieved.records_fetched == 100
        assert retrieved.finished_at is not None

    def test_get_recent_tasks(self, tracer):
        """测试获取最近任务"""
        # 创建多个任务
        for i in range(5):
            task = tracer.start_task(f"task-{i:03d}")
            task.status = "success"
            tracer.finish_task(task)

        # 获取最近 3 个任务
        recent = tracer.get_recent_tasks(limit=3)
        assert len(recent) == 3
        # 应该按时间倒序
        assert recent[0].id == "task-004"
        assert recent[2].id == "task-002"

    def test_add_snapshot(self, tracer):
        """测试添加数据快照"""
        snapshot = DataSnapshot(
            date="2025-01-02",
            schema_name="StockDailySchema",
            partition_key="stock/2025/01",
            record_count=1000,
            source_name="akstock",
        )
        tracer.add_snapshot(snapshot)

        # 验证快照已添加
        snapshots = tracer.get_snapshots("StockDailySchema")
        assert len(snapshots) == 1
        assert snapshots[0].record_count == 1000

    def test_get_all_snapshots(self, tracer):
        """测试获取所有快照"""
        for i in range(3):
            snapshot = DataSnapshot(
                date=f"2025-01-{i+1:02d}",
                schema_name=f"Schema{i}",
                partition_key=f"partition/{i}",
                record_count=100 * i,
                source_name="akstock",
            )
            tracer.add_snapshot(snapshot)

        all_snapshots = tracer.get_snapshots()
        assert len(all_snapshots) == 3


class TestTaskRunModel:
    """测试 TaskRun 模型"""

    def test_create_task_run(self):
        """测试创建 TaskRun"""
        task = TaskRun(
            id="test-001",
            started_at=datetime.now(),
            source_name="akstock",
            status="success",
        )
        assert task.id == "test-001"
        assert task.source_name == "akstock"


class TestDataSnapshotModel:
    """测试 DataSnapshot 模型"""

    def test_create_snapshot(self):
        """测试创建 DataSnapshot"""
        snapshot = DataSnapshot(
            date="2025-01-02",
            schema_name="StockDailySchema",
            partition_key="stock/2025/01",
            record_count=1000,
            source_name="akstock",
        )
        assert snapshot.schema_name == "StockDailySchema"
        assert snapshot.record_count == 1000
