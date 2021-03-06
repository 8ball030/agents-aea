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

"""This package contains a the behaviours."""

import datetime
import logging
import sys
from typing import cast, Optional, TYPE_CHECKING

from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description, DataModel, Attribute
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF
from aea.skills.base import Behaviour

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.protocols.tac.message import TACMessage
    from packages.protocols.tac.serialization import TACSerializer
    from packages.skills.tac_control.game import Game, Phase
    from packages.skills.tac_control.parameters import Parameters
else:
    from tac_protocol.message import TACMessage
    from tac_protocol.serialization import TACSerializer
    from tac_control_skill.game import Game, Phase
    from tac_control_skill.parameters import Parameters

CONTROLLER_DATAMODEL = DataModel("tac", [
    Attribute("version", str, True, "Version number of the TAC Controller Agent."),
])

logger = logging.getLogger("aea.tac_control_skill")


class TACBehaviour(Behaviour):
    """This class implements the TAC control behaviour."""

    def __init__(self, **kwargs):
        """Instantiate the behaviour."""
        super().__init__(**kwargs)
        self._oef_msg_id = 0
        self._registered_desc = None  # type: Optional[Description]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        game = cast(Game, self.context.game)
        parameters = cast(Parameters, self.context.parameters)
        now = datetime.datetime.now()
        if game.phase.value == Phase.PRE_GAME.value and now > parameters.registration_start_time and now < parameters.start_time:
            game.phase = Phase.GAME_REGISTRATION
            self._register_tac()
            logger.info("[{}]: TAC open for registration until: {}".format(self.context.agent_name, parameters.start_time))
        elif game.phase.value == Phase.GAME_REGISTRATION.value and now > parameters.start_time and now < parameters.end_time:
            if game.registration.nb_agents < parameters.min_nb_agents:
                game.phase = Phase.POST_GAME
                self._cancel_tac()
                self._unregister_tac()
            else:
                game.phase = Phase.GAME_SETUP
                self._start_tac()
                self._unregister_tac()
                game.phase = Phase.GAME
        elif game.phase.value == Phase.GAME.value and now > parameters.end_time:
            game.phase = Phase.POST_GAME
            self._cancel_tac()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        if self._registered_desc is not None:
            self._unregister_tac()

    def _register_tac(self) -> None:
        """
        Register on the OEF as a TAC controller agent.

        :return: None.
        """
        self._oef_msg_id += 1
        desc = Description({"version": self.context.parameters.version_id}, data_model=CONTROLLER_DATAMODEL)
        logger.info("[{}]: Registering TAC data model".format(self.context.agent_name))
        oef_msg = OEFMessage(oef_type=OEFMessage.Type.REGISTER_SERVICE,
                             id=self._oef_msg_id,
                             service_description=desc,
                             service_id="")
        self.context.outbox.put_message(to=DEFAULT_OEF,
                                        sender=self.context.agent_public_key,
                                        protocol_id=OEFMessage.protocol_id,
                                        message=OEFSerializer().encode(oef_msg))
        self._registered_desc = desc

    def _unregister_tac(self) -> None:
        """
        Unregister from the OEF as a TAC controller agent.

        :return: None.
        """
        self._oef_msg_id += 1
        logger.info("[{}]: Unregistering TAC data model".format(self.context.agent_name))
        oef_msg = OEFMessage(oef_type=OEFMessage.Type.UNREGISTER_SERVICE,
                             id=self._oef_msg_id,
                             service_description=self._registered_desc,
                             service_id="")
        self.context.outbox.put_message(to=DEFAULT_OEF,
                                        sender=self.context.agent_public_key,
                                        protocol_id=OEFMessage.protocol_id,
                                        message=OEFSerializer().encode(oef_msg))
        self._registered_desc = None

    def _start_tac(self):
        """Create a game and send the game configuration to every registered agent."""
        game = cast(Game, self.context.game)
        game.create()
        logger.info("[{}]: Started competition:\n{}".format(self.context.agent_name, game.holdings_summary))
        logger.info("[{}]: Computed equilibrium:\n{}".format(self.context.agent_name, game.equilibrium_summary))
        for agent_public_key in game.configuration.agent_pbks:
            agent_state = game.current_agent_states[agent_public_key]
            tac_msg = TACMessage(tac_type=TACMessage.Type.GAME_DATA,
                                 amount_by_currency=agent_state.balance_by_currency,
                                 exchange_params_by_currency=agent_state.exchange_params_by_currency,
                                 quantities_by_good_pbk=agent_state.quantities_by_good_pbk,
                                 utility_params_by_good_pbk=agent_state.utility_params_by_good_pbk,
                                 tx_fee=game.configuration.tx_fee,
                                 agent_pbk_to_name=game.configuration.agent_pbk_to_name,
                                 good_pbk_to_name=game.configuration.good_pbk_to_name,
                                 version_id=game.configuration.version_id)
            logger.debug("[{}]: sending game data to '{}': {}"
                         .format(self.context.agent_name, agent_public_key, str(tac_msg)))
            self.context.outbox.put_message(to=agent_public_key,
                                            sender=self.context.agent_public_key,
                                            protocol_id=TACMessage.protocol_id,
                                            message=TACSerializer().encode(tac_msg))

    def _cancel_tac(self):
        """Notify agents that the TAC is cancelled."""
        game = cast(Game, self.context.game)
        logger.info("[{}]: Notifying agents that TAC is cancelled.".format(self.context.agent_name))
        for agent_pbk in game.registration.agent_pbk_to_name.keys():
            tac_msg = TACMessage(tac_type=TACMessage.Type.CANCELLED)
            self.context.outbox.put_message(to=agent_pbk,
                                            sender=self.context.agent_public_key,
                                            protocol_id=TACMessage.protocol_id,
                                            message=TACSerializer().encode(tac_msg))
