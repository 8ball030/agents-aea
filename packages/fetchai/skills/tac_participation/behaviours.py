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

"""This package contains a tac participation behaviour."""

import logging
from typing import cast

from aea.skills.base import Behaviour

from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from packages.fetchai.skills.tac_participation.game import Game, Phase
from packages.fetchai.skills.tac_participation.search import Search

logger = logging.getLogger("aea.tac_participation_skill")


class TACBehaviour(Behaviour):
    """This class scaffolds a behaviour."""

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
        search = cast(Search, self.context.search)
        if game.phase.value == Phase.PRE_GAME.value and search.is_time_to_search():
            self._search_for_tac()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass

    def _search_for_tac(self) -> None:
        """
        Search for active TAC Controller.

        We assume that the controller is registered as a service with the 'tac' data model
        and with an attribute version = expected_version_id.

        :return: None
        """
        game = cast(Game, self.context.game)
        search = cast(Search, self.context.search)
        query = game.get_game_query()
        search_id = search.get_next_id()
        search.ids_for_tac.add(search_id)
        logger.info("[{}]: Searching for TAC, search_id={}".format(self.context.agent_name, search_id))
        oef_msg = OEFMessage(type=OEFMessage.Type.SEARCH_SERVICES,
                             id=search_id,
                             query=query)
        self.context.outbox.put_message(to=DEFAULT_OEF,
                                        sender=self.context.agent_address,
                                        protocol_id=OEFMessage.protocol_id,
                                        message=OEFSerializer().encode(oef_msg))
