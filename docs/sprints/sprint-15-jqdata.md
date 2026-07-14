# Sprint 15: JQData 适配

**Sprint 周期**: 2027-04-15 至 2027-04-28
**状态**: ✅ 完成
**测试数量**: 12 个

---

## 目标

适配 JQData 数据源，支持股票、指数、财务数据。

## 实现的功能

### 1. JQDataClient

- **get_stock_daily()**: 获取股票日线数据
- **get_index_daily()**: 获取指数日线数据
- **get_finance_data()**: 获取财务数据
- **check_health()**: 健康检查

### 2. JQData Mapper

- **map_daily_columns()**: 日线数据列名映射
- **unify_code()**: JQData 格式转内部格式
- **to_jqcode()**: 内部格式转 JQData 格式

### 3. JQDataSource

- 实现 SourceNode 接口
- 支持 stock, index 数据类型
- 支持 DailySchema 和 FinanceSchema

## 新增文件

| 文件 | 说明 |
|------|------|
| src/aistock/sources/jqdata/__init__.py | JQData 模块 |
| src/aistock/sources/jqdata/client.py | JQData API 客户端 |
| src/aistock/sources/jqdata/mapper.py | 数据映射 |
| src/aistock/sources/jqdata/downloader.py | SourceNode 实现 |
| tests/unit/sources/test_jqdata.py | JQData 测试 (12 个) |

## 测试结果

```
12 passed in 0.12s
```

## Git 提交

```
815a070 feat: Sprint 15 - JQData data source adaptation
```

## 经验总结

1. **专业数据源**: JQData 提供专业级数据质量
2. **Token 认证**: 付费数据源需要 Token 认证
3. **代码格式转换**: JQData 使用 XSHE/XSHG 格式，需要转换
