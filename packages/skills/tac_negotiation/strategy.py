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

"""This module contains the abstract class defining an agent's strategy for the TAC."""

from enum import Enum
import logging
import random
import sys
from typing import Dict, Optional, cast, TYPE_CHECKING

from aea.protocols.oef.models import Query, Description
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.skills.base import SharedClass

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.skills.tac_negotiation.helpers import build_goods_description, build_goods_query
    from packages.skills.tac_negotiation.transactions import Transactions
else:
    from tac_negotiation_skill.helpers import build_goods_description, build_goods_query
    from tac_negotiation_skill.transactions import Transactions

logger = logging.getLogger("aea.tac_negotiation_skill")

ROUNDING_ADJUSTMENT = 1


class Strategy(SharedClass):
    """This class defines an abstract strategy for the agent."""

    class RegisterAs(Enum):
        """This class defines the service registration options."""

        SELLER = 'seller'
        BUYER = 'buyer'
        BOTH = 'both'

    class SearchFor(Enum):
        """This class defines the service search options."""

        SELLERS = 'sellers'
        BUYERS = 'buyers'
        BOTH = 'both'

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._register_as = Strategy.RegisterAs(kwargs.pop('register_as')) if 'register_as' in kwargs.keys() else Strategy.RegisterAs.BOTH
        self._search_for = Strategy.SearchFor(kwargs.pop('search_for')) if 'search_for' in kwargs.keys() else Strategy.SearchFor.BOTH
        super().__init__(**kwargs)

    @property
    def is_registering_as_seller(self) -> bool:
        """Check if the agent registers as a seller on the OEF."""
        return self._register_as == Strategy.RegisterAs.SELLER or self._register_as == Strategy.RegisterAs.BUYER

    @property
    def is_searching_for_sellers(self) -> bool:
        """Check if the agent searches for sellers on the OEF."""
        return self._search_for == Strategy.SearchFor.SELLERS or self._search_for == Strategy.SearchFor.BOTH

    @property
    def is_registering_as_buyer(self) -> bool:
        """Check if the agent registers as a buyer on the OEF."""
        return self._register_as == Strategy.RegisterAs.BUYER or self._register_as == Strategy.RegisterAs.BOTH

    @property
    def is_searching_for_buyers(self) -> bool:
        """Check if the agent searches for buyers on the OEF."""
        return self._search_for == Strategy.SearchFor.BUYERS or self._search_for == Strategy.SearchFor.BOTH

    def get_own_service_description(self, is_supply: bool) -> Description:
        """
        Get the description of the supplied goods (as a seller), or the demanded goods (as a buyer).

        :param is_supply: Boolean indicating whether it is supply or demand.

        :return: the description (to advertise on the Service Directory).
        """
        transactions = cast(Transactions, self.context.transactions)
        ownership_state_after_locks = transactions.ownership_state_after_locks(is_seller=is_supply)
        good_pbk_to_quantities = self._supplied_goods(ownership_state_after_locks.quantities_by_good_pbk) if is_supply else self._demanded_goods(ownership_state_after_locks.quantities_by_good_pbk)
        currency = list(ownership_state_after_locks.amount_by_currency.keys())[0]
        desc = build_goods_description(good_pbk_to_quantities=good_pbk_to_quantities, currency=currency, is_supply=is_supply)
        return desc

    def _supplied_goods(self, good_holdings: Dict[str, int]) -> Dict[str, int]:
        """
        Generate a dictionary of quantities which are supplied.

        :param good_holdings: a dictionary of current good holdings
        :return: a dictionary of quantities supplied
        """
        supply = {}  # type: Dict[str, int]
        for good_pbk, quantity in good_holdings.items():
            supply[good_pbk] = quantity - 1 if quantity > 1 else 0
        return supply

    def _demanded_goods(self, good_holdings: Dict[str, int]) -> Dict[str, int]:
        """
        Generate a dictionary of quantities which are demanded.

        :param good_holdings: a dictionary of current good holdings
        :return: a dictionary of quantities supplied
        """
        demand = {}  # type: Dict[str, int]
        for good_pbk in good_holdings.keys():
            demand[good_pbk] = 1
        return demand

    def get_own_services_query(self, is_searching_for_sellers: bool) -> Query:
        """
        Build a query to search for services.

        In particular, build the query to look for agents
            - which supply the agent's demanded goods (i.e. sellers), or
            - which demand the agent's supplied goods (i.e. buyers).

        :param is_searching_for_sellers: Boolean indicating whether the search is for sellers or buyers.

        :return: the Query, or None.
        """
        transactions = cast(Transactions, self.context.transactions)
        ownership_state_after_locks = transactions.ownership_state_after_locks(is_seller=not is_searching_for_sellers)
        good_pbk_to_quantities = self._demanded_goods(ownership_state_after_locks.quantities_by_good_pbk) if is_searching_for_sellers else self._supplied_goods(ownership_state_after_locks.quantities_by_good_pbk)
        currency = list(ownership_state_after_locks.amount_by_currency.keys())[0]
        query = build_goods_query(good_pbks=list(good_pbk_to_quantities.keys()), currency=currency, is_searching_for_sellers=is_searching_for_sellers)
        return query

    def _get_proposal_for_query(self, query: Query, is_seller: bool) -> Optional[Description]:
        """
        Generate proposal (in the form of a description) which matches the query.

        :param query: the query for which to build the proposal
        :is_seller: whether the agent making the proposal is a seller or not

        :return: a description
        """
        candidate_proposals = self._generate_candidate_proposals(is_seller)
        proposals = []
        for proposal in candidate_proposals:
            if not query.check(proposal): continue
            proposals.append(proposal)
        if not proposals:
            return None
        else:
            return random.choice(proposals)

    def get_proposal_for_query(self, query: Query, is_seller: bool) -> Optional[Description]:
        """
        Generate proposal (in the form of a description) which matches the query.

        :param query: the query for which to build the proposal
        :is_seller: whether the agent making the proposal is a seller or not

        :return: a description
        """
        own_service_description = self.get_own_service_description(is_supply=is_seller)
        if not query.check(own_service_description):
            logger.debug("[{}]: Current holdings do not satisfy CFP query.".format(self.context.agent_name))
            return None
        else:
            proposal_description = self._get_proposal_for_query(query, is_seller=is_seller)
            if proposal_description is None:
                logger.debug("[{}]: Current strategy does not generate proposal that satisfies CFP query.".format(self.context.agent_name))
            return proposal_description

    def _generate_candidate_proposals(self, is_seller: bool):
        """
        Generate proposals from the agent in the role of seller/buyer.

        :param is_seller: the bool indicating whether the agent is a seller.

        :return: a list of proposals in Description form
        """
        transactions = cast(Transactions, self.context.transactions)
        ownership_state_after_locks = transactions.ownership_state_after_locks(is_seller=is_seller)
        good_pbk_to_quantities = self._supplied_goods(ownership_state_after_locks.quantities_by_good_pbk) if is_seller else self._demanded_goods(ownership_state_after_locks.quantities_by_good_pbk)
        nil_proposal_dict = {good_pbk: 0 for good_pbk, quantity in good_pbk_to_quantities.items()}  # type: Dict[str, int]
        proposals = []
        seller_tx_fee = self.context.agent_preferences.transaction_fees['seller_tx_fee']
        buyer_tx_fee = self.context.agent_preferences.transaction_fees['buyer_tx_fee']
        currency = list(self.context.agent_ownership_state.amount_by_currency.keys())[0]
        for good_pbk, quantity in good_pbk_to_quantities.items():
            if is_seller and quantity == 0: continue
            proposal_dict = nil_proposal_dict
            proposal_dict[good_pbk] = 1
            proposal = build_goods_description(good_pbk_to_quantities=proposal_dict, currency=currency, is_supply=is_seller)
            if is_seller:
                delta_good_holdings = {good_pbk: quantity * -1 for good_pbk, quantity in proposal_dict.items()}  # type: Dict[str, int]
            else:
                delta_good_holdings = proposal_dict
            marginal_utility_from_delta_good_holdings = self.context.agent_preferences.marginal_utility(ownership_state=ownership_state_after_locks, delta_good_holdings=delta_good_holdings)
            switch = -1 if is_seller else 1
            breakeven_price_rounded = round(marginal_utility_from_delta_good_holdings) * switch
            if is_seller:
                proposal.values["price"] = breakeven_price_rounded + seller_tx_fee + ROUNDING_ADJUSTMENT
            else:
                proposal.values["price"] = breakeven_price_rounded - buyer_tx_fee - ROUNDING_ADJUSTMENT
            proposal.values["seller_tx_fee"] = seller_tx_fee
            proposal.values["buyer_tx_fee"] = buyer_tx_fee
            if not proposal.values["price"] > 0: continue
            proposals.append(proposal)
        return proposals

    def is_profitable_transaction(self, transaction_msg: TransactionMessage, is_seller: bool) -> bool:
        """
        Check if a transaction is profitable.

        Is it a profitable transaction?
        - apply all the locks for role.
        - check if the transaction is consistent with the locks (enough money/holdings)
        - check that we gain score.

        :param transaction_msg: the transaction_msg
        :param is_seller: the bool indicating whether the agent is a seller.

        :return: True if the transaction is good (as stated above), False otherwise.
        """
        transactions = cast(Transactions, self.context.transactions)
        ownership_state_after_locks = transactions.ownership_state_after_locks(is_seller)
        if not ownership_state_after_locks.check_transaction_is_consistent(transaction_msg):
            return False
        proposal_delta_score = self.context.agent_preferences.get_score_diff_from_transaction(ownership_state_after_locks, transaction_msg)
        if proposal_delta_score >= 0:
            return True
        else:
            return False
