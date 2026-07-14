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
from aistock.schemas.futures import FuturesSchema
from aistock.schemas.options import OptionsSchema

SCHEMA_REGISTRY: dict[str, type] = {
    "daily": StockDailySchema,
    "minute": StockMinuteSchema,
    "finance": FinanceSchema,
    "alternative": AlternativeSchema,
    "north_flow": NorthFlowSchema,
    "margin_trade": MarginTradeSchema,
    "reference": ReferenceSchema,
    "convertible_bond": ConvertibleBondSchema,
    "futures": FuturesSchema,
    "options": OptionsSchema,
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
    "FuturesSchema",
    "OptionsSchema",
    "ALTERNATIVE_SCHEMA_MAP",
    "SCHEMA_REGISTRY",
]
