# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""The transaction message module."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union, cast

from aea.crypto.ledger_apis import SUPPORTED_LEDGER_APIS
from aea.mail.base import Address
from aea.protocols.base import Message

TransactionId = str
OFF_CHAIN = 'off_chain'
SUPPORTED_LEDGER_IDS = SUPPORTED_LEDGER_APIS + [OFF_CHAIN]


class TransactionMessage(Message):
    """The transaction message class."""

    protocol_id = "internal"

    class Performative(Enum):
        """Transaction performative."""

        PROPOSE = "propose"
        SIGN = "sign"
        ACCEPT = "accept"
        REJECT = "reject"

    def __init__(self, performative: Union[str, Performative],
                 skill_ids: List[str],
                 transaction_id: TransactionId,
                 sender: Address,
                 counterparty: Address,
                 is_sender_buyer: bool,
                 currency_pbk: str,
                 amount: int,
                 sender_tx_fee: int,
                 counterparty_tx_fee: int,
                 ledger_id: str,
                 info: Optional[Dict[str, Any]] = None,
                 quantities_by_good_pbk: Optional[Dict[str, int]] = None,
                 transaction_digest: Optional[str] = None,
                 **kwargs):
        """
        Instantiate transaction message.

        :param performative: the performative
        :param skill_ids: the skills to receive the transaction message response
        :param transaction_id: the id of the transaction.
        :param sender: the sender of the transaction.
        :param counterparty: the counterparty of the transaction.
        :param is_sender_buyer: whether the transaction is sent by a buyer.
        :param currency_pbk: the currency of the transaction.
        :param sender_tx_fee: the part of the tx fee paid by the sender
        :param counterparty_tx_fee: the part of the tx fee paid by the counterparty
        :param amount: the amount of money involved.
        :param ledger_id: the ledger id
        :param info: a dictionary for arbitrary information
        :param quantities_by_good_pbk: a map from good pbk to the quantity of that good involved in the transaction.
        :param transaction_digest: the transaction digest
        """
        super().__init__(performative=performative,
                         skill_ids=skill_ids,
                         transaction_id=transaction_id,
                         sender=sender,
                         counterparty=counterparty,
                         is_sender_buyer=is_sender_buyer,
                         currency_pbk=currency_pbk,
                         sender_tx_fee=sender_tx_fee,
                         counterparty_tx_fee=counterparty_tx_fee,
                         amount=amount,
                         ledger_id=ledger_id,
                         info=info,
                         quantities_by_good_pbk=quantities_by_good_pbk,
                         transaction_digest=transaction_digest,
                         **kwargs)
        assert self.check_consistency(), "Transaction message initialization inconsistent."

    def check_consistency(self) -> bool:
        """
        Check that the data is consistent.

        :return: bool
        """
        try:
            assert self.is_set("performative")
            assert self.is_set("skill_ids")
            skill_ids = self.get("skill_ids")
            assert type(skill_ids) == list
            assert self.is_set("transaction_id")
            assert self.is_set("sender")
            assert self.is_set("counterparty")
            sender = self.get("sender")
            counterparty = self.get("counterparty")
            assert sender != counterparty
            assert self.is_set("is_sender_buyer")
            assert self.is_set("currency_pbk")
            assert self.is_set("amount")
            amount = self.get("amount")
            amount = cast(int, amount)
            assert amount >= 0
            assert self.is_set("sender_tx_fee")
            sender_tx_fee = self.get("sender_tx_fee")
            sender_tx_fee = cast(int, sender_tx_fee)
            assert sender_tx_fee >= 0
            assert self.is_set("counterparty_tx_fee")
            counterparty_tx_fee = self.get("counterparty_tx_fee")
            counterparty_tx_fee = cast(int, counterparty_tx_fee)
            assert counterparty_tx_fee >= 0
            assert self.is_set("ledger_id")
            ledger_id = self.get("ledger_id")
            assert type(ledger_id) == str and ledger_id in SUPPORTED_LEDGER_IDS
            assert self.is_set("info")
            info = self.get("info")
            if info is not None:
                assert type(info) == dict
                info = cast(Dict, info)
                for key, value in info.items():
                    assert type(key) == str
            assert self.is_set("quantities_by_good_pbk")
            quantities_by_good_pbk = self.get("quantities_by_good_pbk")
            if quantities_by_good_pbk is not None:
                assert type(quantities_by_good_pbk) == dict
                for key, value in quantities_by_good_pbk.items():
                    assert type(key) == str and type(value) == int
                quantities_by_good_pbk = cast(Dict[str, int], quantities_by_good_pbk)
                assert len(quantities_by_good_pbk.keys()) == len(set(quantities_by_good_pbk.keys()))
                assert all(quantity >= 0 for quantity in quantities_by_good_pbk.values())
            assert self.is_set("transaction_digest")
            transaction_digest = self.get("transaction_digest")
            if transaction_digest is not None:
                assert type(transaction_digest) == str
            assert len(self.body) == 14

        except (AssertionError, KeyError):
            return False
        return True

    def matches(self, other: 'TransactionMessage') -> bool:
        """
        Check if the transaction matches with another (mirroring) transaction.

        :param other: the other transaction to match.
        :return: True if the two
        """
        return isinstance(other, TransactionMessage) \
            and self.get("performative") == other.get("performative") \
            and self.get("skill_ids") == other.get("skill_ids") \
            and self.get("transaction_id") == other.get("transaction_id") \
            and self.get("sender") == other.get("counterparty") \
            and self.get("counterparty") == other.get("sender") \
            and self.get("is_sender_buyer") != other.get("is_sender_buyer") \
            and self.get("currency") == other.get("currency") \
            and self.get("amount") == other.get("amount") \
            and self.get("sender_tx_fee") == other.get("counterparty_tx_fee") \
            and self.get("counterparty_tx_fee") == other.get("sender_tx_fee") \
            and self.get("ledger_id") == other.get("ledger_id") \
            and self.get("info") == other.get("info") \
            and self.get("quantities_by_good_pbk") == other.get("quantities_by_good_pbk") \
            and self.get("transaction_digest") == other.get("transaction_digest")

    @classmethod
    def respond_with(cls, other: 'TransactionMessage', performative: Performative, transaction_digest: Optional[str] = None) -> 'TransactionMessage':
        """
        Create response message.

        :param other: TransactionMessage
        :param performative: the performative
        :param transaction_digest: the transaction digest
        :return: a transaction message object
        """
        tx_msg = TransactionMessage(performative=performative,
                                    skill_ids=cast(List[str], other.get("skill_ids")),
                                    transaction_id=cast(str, other.get("transaction_id")),
                                    sender=cast(Address, other.get("sender")),
                                    counterparty=cast(Address, other.get("counterparty")),
                                    is_sender_buyer=cast(bool, other.get("is_sender_buyer")),
                                    currency_pbk=cast(str, other.get("currency_pbk")),
                                    sender_tx_fee=cast(int, other.get("sender_tx_fee")),
                                    counterparty_tx_fee=cast(int, other.get("counterparty_tx_fee")),
                                    amount=cast(int, other.get("amount")),
                                    ledger_id=cast(str, other.get("ledger_id")),
                                    info=cast(Dict[str, Any], other.get("info")),
                                    quantities_by_good_pbk=cast(Dict[str, int], other.get("quantities_by_good_pbk")),
                                    transaction_digest=transaction_digest)
        return tx_msg

    def __eq__(self, other: object) -> bool:
        """
        Compare to another object.

        :param other: the other transaction to match.
        :return: True if the two
        """
        return isinstance(other, TransactionMessage) \
            and self.get("performative") == other.get("performative") \
            and self.get("skill_ids") == other.get("skill_ids") \
            and self.get("transaction_id") == other.get("transaction_id") \
            and self.get("sender") == other.get("sender") \
            and self.get("counterparty") == other.get("counterparty") \
            and self.get("is_sender_buyer") == other.get("is_sender_buyer") \
            and self.get("currency") == other.get("currency") \
            and self.get("amount") == other.get("amount") \
            and self.get("sender_tx_fee") == other.get("sender_tx_fee") \
            and self.get("counterparty_tx_fee") == other.get("counterparty_tx_fee") \
            and self.get("ledger_id") == other.get("ledger_id") \
            and self.get("info") == other.get("info") \
            and self.get("quantities_by_good_pbk") == other.get("quantities_by_good_pbk") \
            and self.get("transaction_digest") == other.get("transaction_digest")
