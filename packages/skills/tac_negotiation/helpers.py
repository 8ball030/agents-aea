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

"""This class contains the helpers for FIPA negotiation."""

import copy
from typing import Dict, List, Union, cast

from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.dialogue.base import DialogueLabel
from aea.protocols.oef.models import Attribute, DataModel, Description, Query, Constraint, ConstraintType, Or, \
    ConstraintExpr

Address = str
TransactionId = str

SUPPLY_DATAMODEL_NAME = 'supply'
DEMAND_DATAMODEL_NAME = 'demand'


def build_goods_datamodel(good_pbks: List[str], is_supply: bool) -> DataModel:
    """
    Build a data model for supply and demand of goods (i.e. for offered or requested goods).

    :param good_pbks: a list of public keys (i.e. identifiers) of the relevant goods.
    :param currency: the currency used for trading.
    :param is_supply: Boolean indicating whether it is a supply or demand data model

    :return: the data model.
    """
    good_quantities_attributes = [Attribute(good_pbk, int, True, "A good on offer.") for good_pbk in good_pbks]
    currency_attribute = Attribute('currency', str, True, "The currency for pricing and transacting the goods.")
    price_attribute = Attribute('price', int, False, "The price of the goods in the currency.")
    seller_tx_fee_attribute = Attribute('seller_tx_fee', int, False, "The transaction fee payable by the seller in the currency.")
    buyer_tx_fee_attribute = Attribute('buyer_tx_fee', int, False, "The transaction fee payable by the buyer in the currency.")
    description = SUPPLY_DATAMODEL_NAME if is_supply else DEMAND_DATAMODEL_NAME
    attributes = good_quantities_attributes + [currency_attribute, price_attribute, seller_tx_fee_attribute, buyer_tx_fee_attribute]
    data_model = DataModel(description, attributes)
    return data_model


def build_goods_description(good_pbk_to_quantities: Dict[str, int], currency: str, is_supply: bool) -> Description:
    """
    Get the service description (good quantities supplied or demanded and their price).

    :param good_pbk_to_quantities: a dictionary mapping the public keys of the goods to the quantities.
    :param currency: the currency used for pricing and transacting.
    :param is_supply: True if the description is indicating supply, False if it's indicating demand.

    :return: the description to advertise on the Service Directory.
    """
    data_model = build_goods_datamodel(good_pbks=list(good_pbk_to_quantities.keys()), is_supply=is_supply)
    values = cast(Dict[str, Union[int, str]], good_pbk_to_quantities)
    values.update({'currency': currency})
    desc = Description(values, data_model=data_model)
    return desc


def build_goods_query(good_pbks: List[str], currency: str, is_searching_for_sellers: bool) -> Query:
    """
    Build buyer or seller search query.

    Specifically, build the search query
        - to look for sellers if the agent is a buyer, or
        - to look for buyers if the agent is a seller.

    In particular, if the agent is a buyer and the demanded good public keys are {'tac_good_0', 'tac_good_2', 'tac_good_3'}, the resulting constraint expression is:

        tac_good_0 >= 1 OR tac_good_2 >= 1 OR tac_good_3 >= 1

    That is, the OEF will return all the sellers that have at least one of the good in the query
    (assuming that the sellers are registered with the data model specified).

    :param good_pbks: the list of good public keys to put in the query
    :param currency: the currency used for pricing and transacting.
    :param is_searching_for_sellers: Boolean indicating whether the query is for sellers (supply) or buyers (demand).

    :return: the query
    """
    data_model = build_goods_datamodel(good_pbks=good_pbks, is_supply=is_searching_for_sellers)
    constraints = [Constraint(good_pbk, ConstraintType(">=", 1)) for good_pbk in good_pbks]
    constraints.append(Constraint('currency', ConstraintType("==", currency)))
    constraint_expr = cast(List[ConstraintExpr], constraints)

    if len(good_pbks) > 1:
        constraint_expr = [Or(constraint_expr)]

    query = Query(constraint_expr, model=data_model)
    return query


def generate_transaction_id(agent_pbk: Address, opponent_pbk: Address, dialogue_label: DialogueLabel, agent_is_seller: bool) -> TransactionId:
    """
    Make a transaction id.

    :param agent_pbk: the pbk of the agent.
    :param opponent_pbk: the public key of the opponent.
    :param dialogue_label: the dialogue label
    :param agent_is_seller: boolean indicating if the agent is a seller
    :return: a transaction id
    """
    # the format is {buyer_pbk}_{seller_pbk}_{dialogue_id}_{dialogue_starter_pbk}
    assert opponent_pbk == dialogue_label.dialogue_opponent_pbk
    buyer_pbk, seller_pbk = (opponent_pbk, agent_pbk) if agent_is_seller else (agent_pbk, opponent_pbk)
    transaction_id = "{}_{}_{}_{}_{}".format(buyer_pbk, seller_pbk, dialogue_label.dialogue_starter_reference, dialogue_label.dialogue_responder_reference, dialogue_label.dialogue_starter_pbk)
    return transaction_id


def dialogue_label_from_transaction_id(agent_pbk: Address, transaction_id: TransactionId) -> DialogueLabel:
    """
    Recover dialogue label from transaction id.

    :param agent_pbk: the pbk of the agent.
    :param transaction_id: the transaction id
    :return: a dialogue label
    """
    buyer_pbk, seller_pbk, dialogue_starter_reference, dialogue_responder_reference, dialogue_starter_pbk = transaction_id.split('_')
    if agent_pbk == buyer_pbk:
        dialogue_opponent_pbk = seller_pbk
    else:
        dialogue_opponent_pbk = buyer_pbk
    dialogue_label = DialogueLabel((dialogue_starter_reference, dialogue_responder_reference), dialogue_opponent_pbk, dialogue_starter_pbk)
    return dialogue_label


def generate_transaction_message(proposal_description: Description, dialogue_label: DialogueLabel, is_seller: bool, agent_public_key: str) -> TransactionMessage:
    """
    Generate the transaction message from the description and the dialogue.

    :param proposal_description: the description of the proposal
    :param dialogue_label: the dialogue label
    :param is_seller: the agent is a seller
    :param agent_public_key: the public key of the agent
    :return: a transaction message
    """
    transaction_id = generate_transaction_id(agent_public_key, dialogue_label.dialogue_opponent_pbk, dialogue_label, is_seller)
    sender_tx_fee = proposal_description.values['seller_tx_fee'] if is_seller else proposal_description.values['buyer_tx_fee']
    counterparty_tx_fee = proposal_description.values['buyer_tx_fee'] if is_seller else proposal_description.values['seller_tx_fee']
    goods_component = copy.copy(proposal_description.values)
    [goods_component.pop(key) for key in ['seller_tx_fee', 'buyer_tx_fee', 'price', 'currency']]
    transaction_msg = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                         skill_id="tac_negotiation_skill",
                                         transaction_id=transaction_id,
                                         sender=agent_public_key,
                                         counterparty=dialogue_label.dialogue_opponent_pbk,
                                         currency_pbk=proposal_description.values['currency'],
                                         amount=proposal_description.values['price'],
                                         is_sender_buyer=not is_seller,
                                         sender_tx_fee=sender_tx_fee,
                                         counterparty_tx_fee=counterparty_tx_fee,
                                         quantities_by_good_pbk=goods_component)
    return transaction_msg
