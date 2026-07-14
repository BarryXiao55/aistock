"""Storage backend router."""

from aistock.exceptions import StoreError


def get_backend(config: dict):
    """根据 pipeline.yaml 中 storage.backend 字段创建后端实例"""
    backend_name = config["storage"]["backend"]
    if backend_name == "parquet":
        from aistock.storage.parquet.backend import ParquetBackend

        return ParquetBackend(config)
    if backend_name == "postgres":
        from aistock.storage.postgres.backend import PostgresBackend  # Phase 2

        return PostgresBackend(config)
    raise StoreError(f"Unknown backend: {backend_name}")
