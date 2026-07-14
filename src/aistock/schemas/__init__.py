"""Internal standard schemas and registry."""

from aistock.schemas.daily import StockDailySchema
from aistock.schemas.minute import StockMinuteSchema
from aistock.schemas.finance import FinanceSchema
from aistock.schemas.alternative import (
    AlternativeSchema,
    NorthFlowSchema,
    MarginTradeSchema,
    ALTERNATIVE_SCHEMA_MAP,
)
from aistock.schemas.reference import ReferenceSchema
from aistock.schemas.convertible_bond import ConvertibleBondSchema

SCHEMA_REGISTRY: dict[str, type] = {
    "daily": StockDailySchema,
    "minute": StockMinuteSchema,
    "finance": FinanceSchema,
    "alternative": AlternativeSchema,
    "north_flow": NorthFlowSchema,
    "margin_trade": MarginTradeSchema,
    "reference": ReferenceSchema,
    "convertible_bond": ConvertibleBondSchema,
}

__all__ = [
    "StockDailySchema",
    "StockMinuteSchema",
    "FinanceSchema",
    "AlternativeSchema",
    "NorthFlowSchema",
    "MarginTradeSchema",
    "ReferenceSchema",
    "ConvertibleBondSchema",
    "ALTERNATIVE_SCHEMA_MAP",
    "SCHEMA_REGISTRY",
]
