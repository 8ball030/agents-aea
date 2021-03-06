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

"""This test module contains the tests for the `aea` sub-commands."""

from ..common.click_testing import CliRunner

import aea
from aea.cli import cli


def test_no_argument():
    """Test that if we run the cli tool without arguments, it exits gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0


def test_flag_version():
    """Test that the flag '--version' works correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.stdout == "aea, version {}\n".format(aea.__version__)


def test_flag_help():
    """Test that the flag '--help' works correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.stdout == """Usage: aea [OPTIONS] COMMAND [ARGS]...

  Command-line tool for setting up an Autonomous Economic Agent.

Options:
  --version            Show the version and exit.
  -v, --verbosity LVL  One of NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL, OFF
  --help               Show this message and exit.

Commands:
  add           Add a resource to the agent.
  add-key       Add a private key to the wallet.
  create        Create an agent.
  delete        Delete an agent.
  freeze        Get the dependencies.
  generate-key  Generate private keys.
  gui           Run the CLI GUI.
  install       Install the dependencies.
  list          List the installed resources.
  remove        Remove a resource from the agent.
  run           Run the agent.
  scaffold      Scaffold a resource for the agent.
  search        Search for components in the registry.
"""
