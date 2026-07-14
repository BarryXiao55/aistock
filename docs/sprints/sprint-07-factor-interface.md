# Sprint 7: 因子接口设计

**Sprint 周期**: 2026-12-24 至 2027-01-06
**状态**: ✅ 完成
**测试数量**: 20 个

---

## 目标

设计因子计算框架接口，包括 FactorCalculator、FactorRegistry 和 FactorMetadata。

## 实现的功能

### 1. FactorCalculator 接口

```python
class FactorCalculator(ABC):
    """因子计算抽象接口"""
    
    @property
    @abstractmethod
    def metadata(self) -> FactorMetadata:
        """获取因子元数据"""
        ...
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算因子值"""
        ...
```

### 2. FactorRegistry 因子注册表

- 注册和管理因子计算器
- 按类别和标签过滤因子
- 全局注册表单例

### 3. 数据模型

- **FactorMetadata**: 因子元数据
- **FactorResult**: 因子计算结果
- **FactorCategory**: 因子类别枚举
- **FactorFrequency**: 因子频率枚举

## 新增文件

| 文件 | 说明 |
|------|------|
| src/aistock/factors/__init__.py | 因子模块 |
| src/aistock/factors/interface.py | FactorCalculator 接口 |
| src/aistock/factors/registry.py | FactorRegistry 注册表 |
| tests/unit/factors/test_interface.py | 因子接口测试 (20 个) |

## 测试结果

```
20 passed in 0.11s
```

## Git 提交

```
3753649 feat: Sprint 7 - Factor calculation interface and registry
```

## 经验总结

1. **接口设计**: 清晰的接口定义是框架的基础
2. **注册表模式**: 因子注册表便于管理和扩展
3. **元数据管理**: 完整的元数据有助于因子管理
