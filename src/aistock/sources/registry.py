"""Source registry --- per-schema-type priority management."""

from aistock.pipeline.source import SourceNode


class SourceRegistry:
    """
    按 Schema 类型维护独立的优先级降级链。
    source_priority.yaml 中每个 section（daily/minute/finance/alternative）
    对应一条降级链，初始化时通过 SCHEMA_REGISTRY 将 section key 映射到 Schema 类。
    """

    def __init__(self, config: dict):
        self._priorities: dict[type, list[tuple[str, int]]] = {}
        self._sources: dict[str, SourceNode] = {}

    def register(self, source: SourceNode, priority: int, schema: type):
        """为指定 Schema 类型注册数据源及优先级"""
        self._sources[source.name] = source
        if schema not in self._priorities:
            self._priorities[schema] = []
        self._priorities[schema].append((source.name, priority))
        self._priorities[schema].sort(key=lambda x: x[1], reverse=True)

    @property
    def primary(self) -> str | None:
        """全局最高优先级数据源（跨所有 Schema 类型）"""
        for priorities in self._priorities.values():
            if priorities:
                return priorities[0][0]
        return None

    def get_all(self, asset_type: str, schema: type) -> list[SourceNode]:
        """按优先级降序返回支持该品种+数据模型的所有源"""
        candidates = self._priorities.get(schema, [])
        return [
            self._sources[name]
            for name, _ in candidates
            if name in self._sources and self._sources[name].supports(asset_type, schema)
        ]
