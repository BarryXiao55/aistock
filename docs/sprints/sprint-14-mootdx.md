# Sprint 14: Mootdx 适配

**Sprint 周期**: 2027-04-01 至 2027-04-14
**状态**: ✅ 完成
**测试数量**: 8 个

---

## 目标

适配 Mootdx 数据源，支持股票、指数数据。

## 实现的功能

### 1. MootdxClient

- **get_stock_daily()**: 获取股票日线数据
- **get_stock_info()**: 获取股票基本信息
- **get_index_daily()**: 获取指数日线数据
- **check_health()**: 健康检查

### 2. Mootdx Mapper

- **map_daily_columns()**: 日线数据列名映射
- **unify_code()**: 代码格式统一

### 3. MootdxSource

- 实现 SourceNode 接口
- 支持 stock, index 数据类型

## 新增文件

| 文件 | 说明 |
|------|------|
| src/aistock/sources/mootdx/__init__.py | Mootdx 模块 |
| src/aistock/sources/mootdx/client.py | Mootdx API 客户端 |
| src/aistock/sources/mootdx/mapper.py | 数据映射 |
| src/aistock/sources/mootdx/downloader.py | SourceNode 实现 |
| tests/unit/sources/test_mootdx.py | Mootdx 测试 (8 个) |

## 测试结果

```
8 passed in 0.11s
```

## Git 提交

```
50dc468 feat: Sprint 14 - Mootdx data source adaptation
```

## 经验总结

1. **通达信数据源**: Mootdx 提供高质量的通达信数据
2. **代码格式统一**: 需要正确处理代码格式转换
3. **健康检查**: 健康检查有助于检测数据源可用性
