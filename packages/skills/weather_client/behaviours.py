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

"""This package contains a scaffold of a behaviour."""
import logging
import sys
from typing import cast, TYPE_CHECKING

from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from aea.skills.base import Behaviour

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.skills.weather_client.strategy import Strategy
else:
    from weather_client_skill.strategy import Strategy

logger = logging.getLogger("aea.weather_client_skill")


class MySearchBehaviour(Behaviour):
    """This class scaffolds a behaviour."""

    def setup(self) -> None:
        """Implement the setup for the behaviour."""
        pass

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_time_to_search():
            query = strategy.get_service_query()
            search_id = strategy.get_next_search_id()
            oef_msg = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES,
                                 id=search_id,
                                 query=query)
            self.context.outbox.put_message(to=DEFAULT_OEF,
                                            sender=self.context.agent_public_key,
                                            protocol_id=OEFMessage.protocol_id,
                                            message=OEFSerializer().encode(oef_msg))

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
