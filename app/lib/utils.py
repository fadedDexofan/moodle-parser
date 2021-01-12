import decimal
from decimal import Decimal
from typing import Union

Number = Union[int, float, Decimal, str]


def decimal_quantize(amount: Number, rounding: str = decimal.ROUND_FLOOR) -> Decimal:
    if isinstance(amount, float):
        amount = str(amount)
    if not isinstance(amount, Decimal):
        amount = Decimal(amount)
    return amount.quantize(Decimal('0.01'), rounding=rounding)
