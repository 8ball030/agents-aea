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

"""This test module contains the tests for the `aea list` sub-command."""
import json
import os
from pathlib import Path

import jsonschema
from ..common.click_testing import CliRunner
from jsonschema import Draft4Validator

from aea.cli import cli
from tests.conftest import AGENT_CONFIGURATION_SCHEMA, CONFIGURATION_SCHEMA_DIR, CLI_LOG_OPTION, CUR_PATH


class TestListProtocols:
    """Test that the command 'aea list protocols' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver("file://{}/".format(Path(CONFIGURATION_SCHEMA_DIR).absolute()), cls.schema)
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        os.chdir(Path(CUR_PATH, "data", "dummy_aea"))
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "list", "protocols"], standalone_mode=False)

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0

    def test_correct_output(self):
        """Test that the command has printed the correct output."""
        compare_text = """------------------------------
Name: default
Description: The default protocol allows for any bytes message.
Version: 0.1.0
------------------------------
------------------------------
Name: fipa
Description: The fipa protocol implements the FIPA ACL.
Version: 0.1.0
------------------------------

"""
        assert self.result.output == compare_text

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)


class TestListConnections:
    """Test that the command 'aea list connections' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver("file://{}/".format(Path(CONFIGURATION_SCHEMA_DIR).absolute()), cls.schema)
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        os.chdir(Path(CUR_PATH, "data", "dummy_aea"))
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "list", "connections"], standalone_mode=False)

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0

    def test_correct_output(self):
        """Test that the command has printed the correct output."""
        compare_text = """------------------------------
Name: local
Description: The local connection provides a stub for an OEF node.
Version: 0.1.0
------------------------------

"""
        assert self.result.output == compare_text

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)


class TestListSkills:
    """Test that the command 'aea list skills' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver("file://{}/".format(Path(CONFIGURATION_SCHEMA_DIR).absolute()), cls.schema)
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        os.chdir(Path(CUR_PATH, "data", "dummy_aea"))
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "list", "skills"], standalone_mode=False)

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0

    def test_correct_output(self):
        """Test that the command has printed the correct output."""
        compare_text = """------------------------------
Name: dummy
Description: a dummy_skill for testing purposes.
Version: 0.1.0
------------------------------
------------------------------
Name: error
Description: The error skill implements basic error handling required by all AEAs.
Version: 0.1.0
------------------------------

"""
        assert self.result.output == compare_text

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
