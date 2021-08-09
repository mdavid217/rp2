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

from abstract_transaction import AbstractTransaction
from configuration import Configuration
from entry_types import TransactionType
from logger import LOGGER
from rp2_error import RP2TypeError, RP2ValueError


class OutTransaction(AbstractTransaction):
    def __init__(
        self,
        configuration: Configuration,
        line: int,
        timestamp: str,
        asset: str,
        exchange: str,
        holder: str,
        transaction_type: str,
        spot_price: float,
        crypto_out_no_fee: float,
        crypto_fee: float,
        crypto_out_with_fee: Optional[float] = None,
        usd_out_no_fee: Optional[float] = None,
        usd_fee: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> None:
        super().__init__(configuration, line, timestamp, asset, transaction_type, spot_price, notes)

        self.__exchange: str = configuration.type_check_exchange("exchange", exchange)
        self.__holder: str = configuration.type_check_holder("holder", holder)
        self.__crypto_out_no_fee: float = configuration.type_check_positive_float("crypto_out_no_fee", crypto_out_no_fee, non_zero=True)
        self.__crypto_fee: float = configuration.type_check_positive_float("crypto_fee", crypto_fee)

        # Crypto out with fee is optional. It can be derived from crypto out (no fee) and crypto fee, however some exchanges
        # provide it anyway. If it is provided use it as given by the exchange, if not compute it.
        if crypto_out_with_fee is None:
            self.__crypto_out_with_fee = self.__crypto_out_no_fee + self.crypto_fee
        else:
            self.__crypto_out_with_fee = configuration.type_check_positive_float("crypto_out_with_fee", crypto_out_with_fee, non_zero=True)

        # USD out without fee and usd fee are optional. They can be derived from crypto out (no fee), spot price and crypto fee,
        # however some exchanges provide them anyway. If they are provided use them as given by the exchange, if not compute them.
        self.__usd_out_no_fee: float
        self.__usd_out_with_fee: float
        if usd_out_no_fee is None:
            self.__usd_out_no_fee = self.__crypto_out_no_fee * self.spot_price
        else:
            self.__usd_out_no_fee = configuration.type_check_positive_float("usd_out_no_fee", usd_out_no_fee, non_zero=True)
        if usd_fee is None:
            self.__usd_fee = self.__crypto_fee * self.spot_price
        else:
            self.__usd_fee = configuration.type_check_positive_float("usd_fee", usd_fee)
        self.__usd_out_with_fee = self.__usd_out_no_fee + self.__usd_fee

        if spot_price == 0:
            raise RP2ValueError(f"{self.asset} {type(self).__name__} at line {self.line} ({self.timestamp}): parameter 'spot_price' cannot be 0")
        if self.transaction_type != TransactionType.DONATE and self.transaction_type != TransactionType.GIFT and self.transaction_type != TransactionType.SELL:
            raise RP2ValueError(f"{self.asset} {type(self).__name__} at line {self.line} ({self.timestamp}): invalid transaction type {self.transaction_type}")

        # If the values provided by the exchange doesn't match the computed one, log a warning.
        if not Configuration.is_equal_within_precision(self.__crypto_out_with_fee, self.__crypto_out_no_fee + self.__crypto_fee, Configuration.USD_PRECISION):
            LOGGER.warning(
                "%s %s at line %d (%s): crypto_out_with_fee != crypto_out_no_fee + crypto_fee: %f != %f",
                self.asset,
                type(self).__name__,
                self.line,
                self.timestamp,
                self.__crypto_out_with_fee,
                self.__crypto_out_no_fee + self.__crypto_fee,
            )

        if not Configuration.is_equal_within_precision(self.__crypto_fee * self.spot_price, self.__usd_fee, Configuration.USD_PRECISION):
            LOGGER.warning(
                "%s %s at line %d (%s): crypto_fee * spot_price != usd_fee: %f != %f",
                self.asset,
                type(self).__name__,
                self.line,
                self.timestamp,
                self.__crypto_fee * self.spot_price,
                self.__usd_fee,
            )

        if not Configuration.is_equal_within_precision(self.__crypto_out_no_fee * self.spot_price, self.__usd_out_no_fee, Configuration.USD_PRECISION):
            LOGGER.warning(
                "%s %s at line %d (%s): crypto_out_no_fee * spot_price != usd_out_no_fee: %f != %f",
                self.asset,
                type(self).__name__,
                self.line,
                self.timestamp,
                self.__crypto_out_no_fee * self.spot_price,
                self.__usd_out_no_fee,
            )

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
            f"exchange={stringify(self.exchange)}",
            f"holder={stringify(self.holder)}",
            f"transaction_type={stringify(self.transaction_type)}",
            f"spot_price={self.spot_price:.4f}",
            f"crypto_out_no_fee={self.crypto_out_no_fee:.8f}",
            f"crypto_fee={self.crypto_fee:.8f}",
            f"is_taxable={stringify(self.is_taxable())}",
            f"usd_taxable_amount={self.usd_taxable_amount:.4f}",
        ]
        if extra_data:
            class_specific_data.extend(extra_data)

        return super().to_string(indent, repr_format, class_specific_data)

    def __str__(self) -> str:
        return self.to_string(indent=0, repr_format=False)

    def __repr__(self) -> str:
        return self.to_string(indent=0, repr_format=True)

    @property
    def exchange(self) -> str:
        return self.__exchange

    @property
    def holder(self) -> str:
        return self.__holder

    @property
    def crypto_out_no_fee(self) -> float:
        return self.__crypto_out_no_fee

    @property
    def crypto_out_with_fee(self) -> float:
        return self.__crypto_out_with_fee

    @property
    def crypto_fee(self) -> float:
        return self.__crypto_fee

    @property
    def usd_out_no_fee(self) -> float:
        return self.__usd_out_no_fee

    @property
    def usd_out_with_fee(self) -> float:
        return self.__usd_out_with_fee

    @property
    def usd_fee(self) -> float:
        return self.__usd_fee

    @property
    def crypto_taxable_amount(self) -> float:
        return self.crypto_balance_change

    @property
    def usd_taxable_amount(self) -> float:
        return self.usd_balance_change

    @property
    def crypto_balance_change(self) -> float:
        return self.crypto_out_with_fee

    @property
    def usd_balance_change(self) -> float:
        return self.usd_out_with_fee

    def is_taxable(self) -> bool:
        return True
