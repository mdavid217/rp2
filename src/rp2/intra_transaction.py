# Copyright 2021 eprbell
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Callable, List, Optional

from rp2.abstract_transaction import AbstractTransaction
from rp2.configuration import Configuration
from rp2.rp2_decimal import ZERO, RP2Decimal
from rp2.rp2_error import RP2TypeError, RP2ValueError


class IntraTransaction(AbstractTransaction):
    def __init__(
        self,
        configuration: Configuration,
        timestamp: str,
        asset: str,
        from_exchange: str,
        from_holder: str,
        to_exchange: str,
        to_holder: str,
        spot_price: Optional[RP2Decimal],
        crypto_sent: RP2Decimal,
        crypto_received: RP2Decimal,
        unique_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> None:
        if spot_price is None:
            # Sometimes, when fee is 0 in IntraTransactions, exchanges don't provide the spot_price: this is OK because
            # if the fee is 0, spot price isn't needed. In this case spot price is assigned 0.
            spot_price = ZERO
        super().__init__(configuration, timestamp, asset, "MOVE", spot_price, unique_id, notes)

        self.__from_exchange: str = configuration.type_check_exchange("from_exchange", from_exchange)
        self.__from_holder: str = configuration.type_check_holder("from_holder", from_holder)
        self.__to_exchange: str = configuration.type_check_exchange("to_exchange", to_exchange)
        self.__to_holder: str = configuration.type_check_holder("to_holder", to_holder)
        self.__crypto_sent: RP2Decimal = configuration.type_check_positive_decimal("crypto_sent", crypto_sent, non_zero=True)
        self.__crypto_received: RP2Decimal = configuration.type_check_positive_decimal("crypto_received", crypto_received)
        self.__crypto_fee: RP2Decimal
        self.__usd_fee: RP2Decimal

        if self.__from_exchange == self.__to_exchange and self.__from_holder == self.__to_holder:
            raise RP2ValueError(
                f"{self.asset} {type(self).__name__} ({self.timestamp}, id {self.unique_id}): from/to exchanges/holders are the same: sending to self"
            )
        if self.__crypto_sent < self.__crypto_received:
            raise RP2ValueError(f"{self.asset} {type(self).__name__} ({self.timestamp}, id {self.unique_id}): crypto sent < crypto received")

        self.__crypto_fee = self.__crypto_sent - self.__crypto_received
        self.__usd_fee = self.__crypto_fee * self.spot_price

    def to_string(self, indent: int = 0, repr_format: bool = True, extra_data: Optional[List[str]] = None) -> str:
        self.configuration.type_check_positive_int("indent", indent)
        self.configuration.type_check_bool("repr_format", repr_format)
        if extra_data and not isinstance(extra_data, List):
            raise RP2TypeError(f"Parameter 'extra_data' is not of type List: {extra_data}")

        class_specific_data: List[str] = []
        stringify: Callable[[Any], str] = repr
        if not repr_format:
            stringify = str
        class_specific_data = [
            f"from_exchange={stringify(self.from_exchange)}",
            f"from_holder={stringify(self.from_holder)}",
            f"to_exchange={stringify(self.to_exchange)}",
            f"to_holder={stringify(self.to_holder)}",
            f"transaction_type={stringify(self.transaction_type)}",
            f"spot_price={self.spot_price:.4f}",
            f"crypto_sent={self.crypto_sent:.8f}",
            f"crypto_received={self.crypto_received:.8f}",
            f"crypto_fee={self.crypto_fee:.8f}",
            f"usd_fee={self.usd_fee:.4f}",
            f"is_taxable={stringify(self.is_taxable())}",
            f"usd_taxable_amount={self.usd_taxable_amount:.4f}",
        ]
        if extra_data:
            class_specific_data.extend(extra_data)

        return super().to_string(indent=indent, repr_format=repr_format, extra_data=class_specific_data)

    @property
    def from_exchange(self) -> str:
        return self.__from_exchange

    @property
    def from_holder(self) -> str:
        return self.__from_holder

    @property
    def to_exchange(self) -> str:
        return self.__to_exchange

    @property
    def to_holder(self) -> str:
        return self.__to_holder

    @property
    def crypto_sent(self) -> RP2Decimal:
        return self.__crypto_sent

    @property
    def crypto_received(self) -> RP2Decimal:
        return self.__crypto_received

    @property
    def crypto_fee(self) -> RP2Decimal:
        return self.__crypto_fee

    @property
    def usd_fee(self) -> RP2Decimal:
        return self.__usd_fee

    @property
    def crypto_taxable_amount(self) -> RP2Decimal:
        return self.crypto_fee

    @property
    def usd_taxable_amount(self) -> RP2Decimal:
        return self.usd_fee

    @property
    def crypto_balance_change(self) -> RP2Decimal:
        return self.crypto_fee

    @property
    def usd_balance_change(self) -> RP2Decimal:
        return self.usd_fee

    def is_taxable(self) -> bool:
        return self.usd_fee > ZERO