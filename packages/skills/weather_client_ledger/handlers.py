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

"""This package contains a scaffold of a handler."""
import logging
import pprint
import sys
from typing import Dict, List, Optional, cast, TYPE_CHECKING

from aea.configurations.base import ProtocolId
from aea.helpers.dialogue.base import DialogueLabel
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description
from aea.skills.base import Handler
from aea.decision_maker.messages.transaction import TransactionMessage

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.skills.weather_client_ledger.dialogues import Dialogue, Dialogues
    from packages.skills.weather_client_ledger.strategy import Strategy
else:
    from weather_client_ledger_skill.dialogues import Dialogue, Dialogues
    from weather_client_ledger_skill.strategy import Strategy

logger = logging.getLogger("aea.weather_client_ledger_skill")


class FIPAHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message, sender: str) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        # convenience representations
        fipa_msg = cast(FIPAMessage, message)
        msg_performative = FIPAMessage.Performative(message.get('performative'))
        message_id = cast(int, message.get("message_id"))

        # recover dialogue
        dialogues = cast(Dialogues, self.context.dialogues)
        if dialogues.is_belonging_to_registered_dialogue(fipa_msg, sender, self.context.agent_public_key):
            dialogue = cast(Dialogue, dialogues.get_dialogue(fipa_msg, sender, self.context.agent_public_key))
            dialogue.incoming_extend(fipa_msg)
        else:
            self._handle_unidentified_dialogue(fipa_msg, sender)
            return

        # handle message
        if msg_performative == FIPAMessage.Performative.PROPOSE:
            self._handle_propose(fipa_msg, sender, message_id, dialogue)
        elif msg_performative == FIPAMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, sender, message_id, dialogue)
        elif msg_performative == FIPAMessage.Performative.MATCH_ACCEPT_W_ADDRESS:
            self._handle_match_accept(fipa_msg, sender, message_id, dialogue)
        elif msg_performative == FIPAMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, sender, message_id, dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, msg: FIPAMessage, sender: str) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        :param sender: the sender
        """
        logger.info("[{}]: unidentified dialogue.".format(self.context.agent_name))
        default_msg = DefaultMessage(type=DefaultMessage.Type.ERROR,
                                     error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE.value,
                                     error_msg="Invalid dialogue.",
                                     error_data="fipa_message")  # TODO: send back FIPASerializer().encode(msg))
        self.context.outbox.put_message(to=sender,
                                        sender=self.context.agent_public_key,
                                        protocol_id=DefaultMessage.protocol_id,
                                        message=DefaultSerializer().encode(default_msg))

    def _handle_propose(self, msg: FIPAMessage, sender: str, message_id: int, dialogue: Dialogue) -> None:
        """
        Handle the propose.

        :param msg: the message
        :param sender: the sender
        :param message_id: the message id
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = message_id + 1
        new_target_id = message_id
        proposals = cast(List[Description], msg.get("proposal"))

        if proposals is not []:
            # only take the first proposal
            proposal = proposals[0]
            logger.info("[{}]: received proposal={} from sender={}".format(self.context.agent_name,
                                                                           proposal.values,
                                                                           sender[-5:]))
            strategy = cast(Strategy, self.context.strategy)
            acceptable = strategy.is_acceptable_proposal(proposal)
            affordable = strategy.is_affordable_proposal(proposal)
            if acceptable and affordable:
                strategy.is_searching = False
                logger.info("[{}]: accepting the proposal from sender={}".format(self.context.agent_name,
                                                                                 sender[-5:]))
                dialogue.proposal = proposal
                accept_msg = FIPAMessage(message_id=new_message_id,
                                         dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                         target=new_target_id,
                                         performative=FIPAMessage.Performative.ACCEPT)
                dialogue.outgoing_extend(accept_msg)
                self.context.outbox.put_message(to=sender,
                                                sender=self.context.agent_public_key,
                                                protocol_id=FIPAMessage.protocol_id,
                                                message=FIPASerializer().encode(accept_msg))
            else:
                logger.info("[{}]: declining the proposal from sender={}".format(self.context.agent_name,
                                                                                 sender[-5:]))
                decline_msg = FIPAMessage(message_id=new_message_id,
                                          dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                          target=new_target_id,
                                          performative=FIPAMessage.Performative.DECLINE)
                dialogue.outgoing_extend(decline_msg)
                self.context.outbox.put_message(to=sender,
                                                sender=self.context.agent_public_key,
                                                protocol_id=FIPAMessage.protocol_id,
                                                message=FIPASerializer().encode(decline_msg))

    def _handle_decline(self, msg: FIPAMessage, sender: str, message_id: int, dialogue: Dialogue) -> None:
        """
        Handle the decline.

        :param msg: the message
        :param sender: the sender
        :param message_id: the message id
        :param dialogue: the dialogue object
        :return: None
        """
        logger.info("[{}]: received DECLINE from sender={}".format(self.context.agent_name, sender[-5:]))
        # target = msg.get("target")
        # dialogues = cast(Dialogues, self.context.dialogues)
        # if target == 1:
        #     dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_CFP)
        # elif target == 3:
        #     dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_ACCEPT)

    def _handle_match_accept(self, msg: FIPAMessage, sender: str, message_id: int,
                             dialogue: Dialogue) -> None:
        """
        Handle the match accept.

        :param msg: the message
        :param sender: the sender
        :param message_id: the message id
        :param dialogue: the dialogue object
        :return: None
        """
        logger.info("[{}]: received MATCH_ACCEPT_W_ADDRESS from sender={}".format(self.context.agent_name, sender[-5:]))
        address = cast(str, msg.get("address"))
        strategy = cast(Strategy, self.context.strategy)
        proposal = cast(Description, dialogue.proposal)
        ledger_id = cast(str, proposal.values.get("ledger_id"))
        tx_msg = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                    skill_id="weather_client_ledger",
                                    transaction_id="transaction0",
                                    sender=self.context.agent_public_keys[ledger_id],
                                    counterparty=address,
                                    is_sender_buyer=True,
                                    currency_pbk=proposal.values['currency_pbk'],
                                    amount=proposal.values['price'],
                                    sender_tx_fee=strategy.max_buyer_tx_fee,
                                    counterparty_tx_fee=proposal.values['seller_tx_fee'],
                                    quantities_by_good_pbk={},
                                    dialogue_label=dialogue.dialogue_label.json,
                                    ledger_id=ledger_id)
        self.context.decision_maker_message_queue.put_nowait(tx_msg)
        logger.info("[{}]: proposing the transaction to the decision maker. Waiting for confirmation ...".format(
            self.context.agent_name))

    def _handle_inform(self, msg: FIPAMessage, sender: str, message_id: int, dialogue: Dialogue) -> None:
        """
        Handle the match inform.

        :param msg: the message
        :param sender: the sender
        :param message_id: the message id
        :param dialogue: the dialogue object
        :return: None
        """
        logger.info("[{}]: received INFORM from sender={}".format(self.context.agent_name, sender[-5:]))
        json_data = cast(dict, msg.get("json_data"))
        if 'weather_data' in json_data.keys():
            weather_data = json_data['weather_data']
            logger.info("[{}]: received the following weather data={}".format(self.context.agent_name,
                                                                              pprint.pformat(weather_data)))
            # dialogues = cast(Dialogues, self.context.dialogues)
            # dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.SUCCESSFUL)
        else:
            logger.info("[{}]: received no data from sender={}".format(self.context.agent_name,
                                                                       sender[-5:]))


class OEFHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = OEFMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle(self, message: Message, sender: str) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        # convenience representations
        oef_msg = cast(OEFMessage, message)
        oef_msg_type = OEFMessage.Type(oef_msg.get("type"))

        if oef_msg_type is OEFMessage.Type.SEARCH_RESULT:
            agents = cast(List[str], oef_msg.get("agents"))
            self._handle_search(agents)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_search(self, agents: List[str]) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :return: None
        """
        if len(agents) > 0:
            logger.info("[{}]: found agents={}, stopping search.".format(self.context.agent_name, list(map(lambda x: x[-5:], agents))))
            strategy = cast(Strategy, self.context.strategy)
            # stopping search
            strategy.is_searching = False
            # pick first agent found
            opponent_pbk = agents[0]
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogue = dialogues.create_self_initiated(opponent_pbk, self.context.agent_public_key, is_seller=False)
            query = strategy.get_service_query()
            logger.info("[{}]: sending CFP to agent={}".format(self.context.agent_name, opponent_pbk[-5:]))
            cfp_msg = FIPAMessage(message_id=FIPAMessage.STARTING_MESSAGE_ID,
                                  dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                  performative=FIPAMessage.Performative.CFP,
                                  target=FIPAMessage.STARTING_TARGET,
                                  query=query)
            dialogue.outgoing_extend(cfp_msg)
            self.context.outbox.put_message(to=opponent_pbk,
                                            sender=self.context.agent_public_key,
                                            protocol_id=FIPAMessage.protocol_id,
                                            message=FIPASerializer().encode(cfp_msg))
        else:
            logger.info("[{}]: found no agents, continue searching.".format(self.context.agent_name))


class MyTransactionHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = TransactionMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message, sender: str) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        tx_msg_response = cast(TransactionMessage, message)
        if tx_msg_response is not None and \
                TransactionMessage.Performative(tx_msg_response.get("performative")) == TransactionMessage.Performative.ACCEPT:
            logger.info("[{}]: transaction was successful.".format(self.context.agent_name))
            json_data = {'transaction_digest': tx_msg_response.get("transaction_digest")}
            dialogue_label = DialogueLabel.from_json(cast(Dict[str, str], tx_msg_response.get("dialogue_label")))
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogue = dialogues.dialogues[dialogue_label]
            fipa_msg = cast(FIPAMessage, dialogue.last_incoming_message)
            new_message_id = cast(int, fipa_msg.get("message_id")) + 1
            new_target_id = cast(int, fipa_msg.get("target")) + 1
            counterparty_pbk = dialogue.dialogue_label.dialogue_opponent_pbk
            inform_msg = FIPAMessage(message_id=new_message_id,
                                     dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                     target=new_target_id,
                                     performative=FIPAMessage.Performative.INFORM,
                                     json_data=json_data)
            dialogue.outgoing_extend(inform_msg)
            self.context.outbox.put_message(to=counterparty_pbk,
                                            sender=self.context.agent_public_key,
                                            protocol_id=FIPAMessage.protocol_id,
                                            message=FIPASerializer().encode(inform_msg))
            logger.info("[{}]: informing counterparty={} of transaction digest.".format(self.context.agent_name, counterparty_pbk[-5:]))
            self._received_tx_message = True
        else:
            logger.info("[{}]: transaction was not successful.".format(self.context.agent_name))

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
