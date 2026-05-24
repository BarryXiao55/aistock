# ADR-001: 插件化管道架构

**日期**: 2026-05-24
**状态**: 已采纳

## 背景

Aistock 需要接入多个免费数据源（AkShare、Baostock、Tushare），历史下载 + 日常更新，并对数据清洗、标准化后写入本地存储。后期可能扩展更多数据源和 PostgreSQL 后端。

## 决策

采用**插件化管道架构**（方案 B），定义三阶段抽象接口 `SourceNode → Cleaner → StorageBackend`，每个数据源作为独立插件实现 `SourceNode`，通过注册表按优先级编排。

## 备选方案

| 方案 | 描述 | 未选理由 |
|------|------|----------|
| A: 模块化单项目 | 一个包，按职责分模块，CLI 驱动 | 模块间易耦合，扩展数据源时牵一发动全身 |
| C: DAG 编排引擎 | Prefect/Airflow 任务编排 | 太重，前期过度设计 |

## 影响

- 每个数据源独立子包，加源不改框架
- 存储后端可替换（Phase 1 Parquet → Phase 2 PostgreSQL），上层零改动
- 清洗步骤可插拔（`CleaningStep` 接口 + 注册链）
- 后期自动化调度可在框架外侧包 Prefect/Dagster，核心代码不变
