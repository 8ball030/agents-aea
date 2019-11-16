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

"""This module contains the tests for the Multiplexer."""
import asyncio
import shutil
import tempfile
import time
import unittest.mock
from pathlib import Path
from threading import Thread

import pytest

import aea
from aea.connections.local.connection import LocalNode, OEFLocalConnection
from aea.connections.stub.connection import StubConnection
from aea.mail.base import Multiplexer, AEAConnectionError, Envelope, EnvelopeContext
from .conftest import DummyConnection


@pytest.mark.asyncio
async def test_receiving_loop_terminated():
    """Test that connecting twice the multiplexer behaves correctly."""
    multiplexer = Multiplexer([DummyConnection()])
    multiplexer.connect()

    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        multiplexer.connection_status.is_connected = False
        await multiplexer._recv_loop()
        mock_logger_debug.assert_called_with("Receiving loop terminated.")
        multiplexer.connection_status.is_connected = True
        multiplexer.disconnect()


def test_connect_twice():
    """Test that connecting twice the multiplexer behaves correctly."""
    multiplexer = Multiplexer([DummyConnection()])

    assert not multiplexer.connection_status.is_connected
    multiplexer.connect()
    assert multiplexer.connection_status.is_connected
    multiplexer.connect()
    assert multiplexer.connection_status.is_connected

    multiplexer.disconnect()


def test_connect_twice_with_loop():
    """Test that connecting twice the multiplexer behaves correctly."""
    running_loop = asyncio.new_event_loop()
    thread_loop = Thread(target=running_loop.run_forever)
    thread_loop.start()

    multiplexer = Multiplexer([DummyConnection()], loop=running_loop)

    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        assert not multiplexer.connection_status.is_connected
        multiplexer.connect()
        assert multiplexer.connection_status.is_connected
        multiplexer.connect()
        assert multiplexer.connection_status.is_connected

        mock_logger_debug.assert_called_with("Multiplexer already connected.")

        multiplexer.disconnect()
        running_loop.call_soon_threadsafe(running_loop.stop)


@pytest.mark.asyncio
async def test_connect_twice_a_single_connection():
    """Test that connecting twice a single connection behaves correctly."""
    multiplexer = Multiplexer([DummyConnection()])

    assert not multiplexer.connection_status.is_connected
    await multiplexer._connect_one("dummy")
    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        await multiplexer._connect_one("dummy")
        mock_logger_debug.assert_called_with("Connection dummy already established.")
        await multiplexer._disconnect_one("dummy")


def test_multiplexer_connect_all_raises_error():
    """Test the case when the multiplexer raises an exception while connecting."""
    multiplexer = Multiplexer([DummyConnection()])

    with unittest.mock.patch.object(multiplexer, "_connect_all", side_effect=Exception):
        with pytest.raises(AEAConnectionError, match="Failed to connect the multiplexer."):
            multiplexer.connect()


def test_multiplexer_connect_one_raises_error_many_connections():
    """Test the case when the multiplexer raises an exception while attempting the connection of one connection."""
    node = LocalNode()
    tmpdir = Path(tempfile.mktemp())
    d = tmpdir / "test_stub"
    d.mkdir(parents=True)
    input_file_path = d / "input_file.csv"
    output_file_path = d / "input_file.csv"

    connection_1 = OEFLocalConnection("my_pbk", node)
    connection_2 = StubConnection(input_file_path, output_file_path)
    connection_3 = DummyConnection()
    multiplexer = Multiplexer([connection_1, connection_2, connection_3])

    assert not connection_1.connection_status.is_connected
    assert not connection_2.connection_status.is_connected
    assert not connection_3.connection_status.is_connected

    with unittest.mock.patch.object(connection_3, "connect", side_effect=Exception):
        with pytest.raises(AEAConnectionError, match="Failed to connect the multiplexer."):
            multiplexer.connect()

    assert not connection_1.connection_status.is_connected
    assert not connection_2.connection_status.is_connected
    assert not connection_3.connection_status.is_connected

    shutil.rmtree(tmpdir)


@pytest.mark.asyncio
async def test_disconnect_twice_a_single_connection():
    """Test that connecting twice a single connection behaves correctly."""
    multiplexer = Multiplexer([DummyConnection()])

    assert not multiplexer.connection_status.is_connected
    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        await multiplexer._disconnect_one("dummy")
        mock_logger_debug.assert_called_with("Connection dummy already disconnected.")


def test_multiplexer_disconnect_all_raises_error():
    """Test the case when the multiplexer raises an exception while disconnecting."""
    multiplexer = Multiplexer([DummyConnection()])
    multiplexer.connect()

    assert multiplexer.connection_status.is_connected

    with unittest.mock.patch.object(multiplexer, "_disconnect_all", side_effect=Exception):
        with pytest.raises(AEAConnectionError, match="Failed to disconnect the multiplexer."):
            multiplexer.disconnect()

    # TODO is this what we want?
    assert multiplexer.connection_status.is_connected


def test_multiplexer_disconnect_one_raises_error_many_connections():
    """Test the case when the multiplexer raises an exception while attempting the disconnection of one connection."""
    node = LocalNode()
    tmpdir = Path(tempfile.mktemp())
    d = tmpdir / "test_stub"
    d.mkdir(parents=True)
    input_file_path = d / "input_file.csv"
    output_file_path = d / "input_file.csv"

    connection_1 = OEFLocalConnection("my_pbk", node)
    connection_2 = StubConnection(input_file_path, output_file_path)
    connection_3 = DummyConnection()
    multiplexer = Multiplexer([connection_1, connection_2, connection_3])

    assert not connection_1.connection_status.is_connected
    assert not connection_2.connection_status.is_connected
    assert not connection_3.connection_status.is_connected

    multiplexer.connect()

    assert connection_1.connection_status.is_connected
    assert connection_2.connection_status.is_connected
    assert connection_3.connection_status.is_connected

    with unittest.mock.patch.object(connection_3, "disconnect", side_effect=Exception):
        # with pytest.raises(AEAConnectionError, match="Failed to disconnect the multiplexer."):
        multiplexer.disconnect()

    # TODO is this what we want?
    assert not connection_1.connection_status.is_connected
    assert not connection_2.connection_status.is_connected
    assert connection_3.connection_status.is_connected

    shutil.rmtree(tmpdir)


@pytest.mark.asyncio
async def test_sending_loop_does_not_start_if_multiplexer_not_connected():
    """Test that the sending loop is stopped does not start if the multiplexer is not connected."""
    multiplexer = Multiplexer([DummyConnection(connection_id="dummy")])

    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        await multiplexer._send_loop()
        mock_logger_debug.assert_called_with("Sending loop not started. The multiplexer is not connected.")


@pytest.mark.asyncio
async def test_sending_loop_cancelled():
    """Test the case when the sending loop is cancelled."""
    multiplexer = Multiplexer([DummyConnection(connection_id="dummy")])

    multiplexer.connect()

    with unittest.mock.patch.object(aea.mail.base.logger, "debug") as mock_logger_debug:
        multiplexer._send_loop_task.cancel()
        await asyncio.sleep(0.1)
        mock_logger_debug.assert_called_with("Sending loop cancelled.")

    multiplexer.disconnect()


@pytest.mark.asyncio
async def test_receiving_loop_raises_exception():
    """Test the case when an error occurs when a receive is started."""
    connection = DummyConnection(connection_id="dummy")
    multiplexer = Multiplexer([connection])

    with unittest.mock.patch("asyncio.wait", side_effect=Exception("a weird error.")):
        with unittest.mock.patch.object(aea.mail.base.logger, "error") as mock_logger_error:
            multiplexer.connect()
            time.sleep(0.1)
            mock_logger_error.assert_called_with("Error in the receiving loop: a weird error.")

    multiplexer.disconnect()


@pytest.mark.asyncio
async def test_send_envelope_with_non_registered_connection():
    """Test that sending an envelope with an unregistered connection raises an exception."""
    connection = DummyConnection(connection_id="dummy")
    multiplexer = Multiplexer([connection])
    multiplexer.connect()

    envelope = Envelope(to="", sender="", protocol_id="default", message=b"",
                        context=EnvelopeContext(connection_id="this_is_an_unexisting_connection_id"))

    with pytest.raises(AEAConnectionError, match="No connection registered with id:.*"):
        await multiplexer._send(envelope)

    multiplexer.disconnect()


def test_send_envelope_error_is_logged_by_send_loop():
    """Test that the AEAConnectionError in the '_send' method is logged by the '_send_loop'."""
    connection = DummyConnection(connection_id="dummy")
    multiplexer = Multiplexer([connection])
    multiplexer.connect()

    envelope = Envelope(to="", sender="", protocol_id="default", message=b"",
                        context=EnvelopeContext(connection_id="this_is_an_unexisting_connection_id"))

    with unittest.mock.patch.object(aea.mail.base.logger, "error") as mock_logger_error:
        multiplexer.put(envelope)
        time.sleep(0.1)
        mock_logger_error.assert_called_with("No connection registered with id: this_is_an_unexisting_connection_id.")

    multiplexer.disconnect()


def test_get_from_multiplexer_when_empty():
    """Test that getting an envelope from the multiplexer when the input queue is empty raises an exception."""
    connection = DummyConnection(connection_id="dummy")
    multiplexer = Multiplexer([connection])

    with pytest.raises(aea.mail.base.Empty):
        multiplexer.get()
