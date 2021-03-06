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

"""This test module contains the tests for the `aea remove connection` sub-command."""
import os
import shutil
import tempfile
import unittest.mock
from pathlib import Path

import yaml
from ...common.click_testing import CliRunner

import aea
import aea.cli.common
import aea.configurations.base
from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from tests.conftest import CLI_LOG_OPTION


class TestRemoveConnection:
    """Test that the command 'aea remove connection' works correctly."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_name = "local"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False)
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", cls.connection_name], standalone_mode=False)
        assert result.exit_code == 0
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "remove", "connection", cls.connection_name], standalone_mode=False)

    def test_exit_code_equal_to_zero(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 0

    def test_directory_does_not_exist(self):
        """Test that the directory of the removed connection does not exist."""
        assert not Path("connections", self.connection_name).exists()

    def test_connection_not_present_in_agent_config(self):
        """Test that the name of the removed connection is not present in the agent configuration file."""
        agent_config = aea.configurations.base.AgentConfig.from_json(yaml.safe_load(open(DEFAULT_AEA_CONFIG_FILE)))
        assert self.connection_name not in agent_config.connections

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRemoveConnectionFailsWhenConnectionDoesNotExist:
    """Test that the command 'aea remove connection' fails when the connection does not exist."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_name = "local"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False)
        assert result.exit_code == 0
        os.chdir(cls.agent_name)

        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "remove", "connection", cls.connection_name], standalone_mode=False)

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_connection_not_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'Connection '{connection_name}' not found.'
        """
        s = "Connection '{}' not found.".format(self.connection_name)
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestRemoveConnectionFailsWhenExceptionOccurs:
    """Test that the command 'aea remove connection' fails when an exception occurs while removing the directory."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.connection_name = "local"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False)
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", cls.connection_name], standalone_mode=False)
        assert result.exit_code == 0

        cls.patch = unittest.mock.patch("shutil.rmtree", side_effect=BaseException("an exception"))
        cls.patch.__enter__()

        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "remove", "connection", cls.connection_name], standalone_mode=False)

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        cls.patch.__exit__()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
