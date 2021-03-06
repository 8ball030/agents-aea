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

"""This test module contains the tests for the `aea generate-key` sub-command."""
import os
import shutil
import tempfile
from pathlib import Path

from ..common.click_testing import CliRunner

from aea.cli import cli
from aea.crypto.default import DefaultCrypto
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.helpers import DEFAULT_PRIVATE_KEY_FILE, FETCHAI_PRIVATE_KEY_FILE, ETHEREUM_PRIVATE_KEY_FILE
from tests.conftest import CLI_LOG_OPTION


class TestGenerateKey:
    """Test that the command 'aea generate-key' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_default(self):
        """Test that the default private key is created correctly."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", "default"])
        assert result.exit_code == 0
        assert Path(DEFAULT_PRIVATE_KEY_FILE).exists()
        DefaultCrypto(DEFAULT_PRIVATE_KEY_FILE)

        Path(DEFAULT_PRIVATE_KEY_FILE).unlink()

    def test_fetch(self):
        """Test that the fetch private key is created correctly."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", "fetchai"])
        assert result.exit_code == 0
        assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()
        FetchAICrypto(FETCHAI_PRIVATE_KEY_FILE)

        Path(FETCHAI_PRIVATE_KEY_FILE).unlink()

    def test_ethereum(self):
        """Test that the fetch private key is created correctly."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", "ethereum"])
        assert result.exit_code == 0
        assert Path(ETHEREUM_PRIVATE_KEY_FILE).exists()
        EthereumCrypto(ETHEREUM_PRIVATE_KEY_FILE)

        Path(ETHEREUM_PRIVATE_KEY_FILE).unlink()

    def test_all(self):
        """Test that all the private keys are created correctly when running 'aea generate-key all'."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", "all"])
        assert result.exit_code == 0

        assert Path(DEFAULT_PRIVATE_KEY_FILE).exists()
        assert Path(FETCHAI_PRIVATE_KEY_FILE).exists()
        assert Path(ETHEREUM_PRIVATE_KEY_FILE).exists()
        DefaultCrypto(DEFAULT_PRIVATE_KEY_FILE)
        FetchAICrypto(FETCHAI_PRIVATE_KEY_FILE)
        EthereumCrypto(ETHEREUM_PRIVATE_KEY_FILE)

        Path(DEFAULT_PRIVATE_KEY_FILE).unlink()
        Path(FETCHAI_PRIVATE_KEY_FILE).unlink()
        Path(ETHEREUM_PRIVATE_KEY_FILE).unlink()

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        shutil.rmtree(cls.t)
