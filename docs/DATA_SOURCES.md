# 数据源功能说明

## 概述

Aistock 支持多个数据源，提供 A 股市场数据的采集能力。每个数据源作为独立插件实现，通过统一接口集成到数据管道中。

## 支持的数据源

### 1. AkShare (主力数据源)

**类型**: 免费
**特点**: 无需注册，API 简洁

| 功能 | 支持 |
|------|------|
| 股票日线 | ✅ |
| 股票分钟线 | ✅ |
| 指数数据 | ✅ |
| ETF 数据 | ✅ |
| 期货数据 | ✅ |
| 财务数据 | ✅ |
| 北向资金 | ✅ |
| 融资融券 | ✅ |

**配置**: 无需额外配置

### 2. Baostock (备份数据源)

**类型**: 免费
**特点**: 数据质量高，稳定性好

| 功能 | 支持 |
|------|------|
| 股票日线 | ✅ |
| 指数数据 | ✅ |
| 复权数据 | ✅ |

**配置**: 无需额外配置

### 3. Tushare (可选增强)

**类型**: 付费
**特点**: 数据丰富，需要 token

| 功能 | 支持 |
|------|------|
| 股票日线 | ✅ |
| 股票分钟线 | ✅ |
| 财务数据 | ✅ |
| 因子数据 | ✅ |

**配置**:
```yaml
tushare:
  token: ${TUSHARE_TOKEN}
```

### 4. EFinance (免费)

**类型**: 免费
**特点**: 基于东方财富，API 简洁

| 功能 | 支持 |
|------|------|
| 股票日线 | ✅ |
| 基金净值 | ✅ |
| 期货数据 | ✅ |
| 实时行情 | ✅ |

**配置**: 无需额外配置

### 5. Mootdx (免费)

**类型**: 免费
**特点**: 通达信数据源，数据质量高

| 功能 | 支持 |
|------|------|
| 股票日线 | ✅ |
| 指数数据 | ✅ |
| 复权数据 | ✅ |

**配置**: 无需额外配置

### 6. JQData (付费)

**类型**: 付费
**特点**: 专业级数据，因子数据丰富

| 功能 | 支持 |
|------|------|
| 股票日线 | ✅ |
| 股票分钟线 | ✅ |
| 财务数据 | ✅ |
| 因子数据 | ✅ |

**配置**:
```yaml
jqdata:
  token: ${JQDATA_TOKEN}
```

## 数据源优先级

在 `config/source_priority.yaml` 中配置数据源优先级：

```yaml
daily:
  - name: akstock
    priority: 100
  - name: baostock
    priority: 80
  - name: tushare
    priority: 50
  - name: efinance
    priority: 100
  - name: mootdx
    priority: 100
  - name: jqdata
    priority: 100
```

## 降级链

当主数据源不可用时，系统会自动降级到下一个数据源：

```
AkShare (优先级 100) → Baostock (优先级 80) → Tushare (优先级 50)
```

## 使用示例

### 1. 配置数据源

编辑 `config/source_priority.yaml`：

```yaml
daily:
  - name: akstock
    priority: 100
    config: {}
  - name: efinance
    priority: 90
    config: {}
  - name: mootdx
    priority: 80
    config: {}
```

### 2. 使用数据源

```python
from aistock.sources.registry import SourceRegistry
from aistock.sources.akstock.downloader import AkStockSource
from aistock.sources.efinance.downloader import EFinanceSource

# 创建注册表
registry = SourceRegistry({})

# 注册数据源
registry.register(AkStockSource(), priority=100, schema=StockDailySchema)
registry.register(EFinanceSource(), priority=90, schema=StockDailySchema)

# 获取数据源
sources = registry.get_all("stock", StockDailySchema)
```

### 3. 自定义数据源

```python
from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec

class MyCustomSource(SourceNode):
    """自定义数据源"""
    name = "custom"
    
    def supports(self, asset_type: str, schema: type) -> bool:
        """声明支持的数据类型"""
        return asset_type == "stock" and schema == StockDailySchema
    
    def fetch(self, spec: FetchSpec) -> pd.DataFrame:
        """执行数据下载"""
        # 实现数据下载逻辑
        ...
```

## 扩展指南

### 添加新数据源

1. 创建数据源目录 `src/aistock/sources/<name>/`
2. 实现 `client.py` - API 封装
3. 实现 `mapper.py` - 字段映射
4. 实现 `downloader.py` - SourceNode 接口
5. 更新 `config/source_priority.yaml` 配置优先级

### 数据源接口

所有数据源必须实现 `SourceNode` 接口：

```python
class SourceNode(ABC):
    """数据源抽象接口"""
    name: str
    
    @abstractmethod
    def supports(self, asset_type: str, schema: type) -> bool:
        """声明支持的数据类型"""
        ...
    
    @abstractmethod
    def fetch(self, spec: FetchSpec) -> pd.DataFrame:
        """执行数据下载"""
        ...
    
    def check_health(self) -> bool:
        """健康检查"""
        return True
```

## 测试

```bash
# 运行数据源单元测试
pytest tests/unit/sources/ -v

# 运行数据源集成测试
pytest tests/integration/sources/ -v
```

## 注意事项

1. **API 限制**: 免费数据源可能有请求频率限制
2. **Token 配置**: 付费数据源需要配置 token
3. **网络连接**: 数据源需要网络连接
4. **数据质量**: 不同数据源的数据质量可能不同
