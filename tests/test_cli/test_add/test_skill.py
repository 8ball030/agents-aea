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

"""This test module contains the tests for the `aea add skill` sub-command."""
import os
import shutil
import tempfile
import unittest.mock
from pathlib import Path

import yaml
from ...common.click_testing import CliRunner
from jsonschema import ValidationError

import aea
import aea.cli.common
from aea.cli import cli
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE
from tests.conftest import ROOT_DIR, CLI_LOG_OPTION


class TestAddSkillFailsWhenSkillAlreadyExists:
    """Test that the command 'aea add skill' fails when the skill already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_name = "error"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False)
        # this also by default adds the oef connection and error skill
        assert result.exit_code == 0
        os.chdir(cls.agent_name)

        # change default registry path
        config = AgentConfig.from_json(yaml.safe_load(open(DEFAULT_AEA_CONFIG_FILE)))
        config.registry_path = os.path.join(ROOT_DIR, "packages")
        yaml.safe_dump(config.json, open(DEFAULT_AEA_CONFIG_FILE, "w"))

        # add the error skill again
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", cls.skill_name], standalone_mode=False)

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_skill_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'A skill with name '{skill_name}' already exists. Aborting...'
        """
        s = "A skill with name '{}' already exists. Aborting...".format(self.skill_name)
        self.mocked_logger_error.assert_called_once_with(s)

    @unittest.mock.patch(
        'aea.cli.add.split_public_id',
        return_value=['owner', 'name', 'version']
    )
    @unittest.mock.patch('aea.cli.add.fetch_package')
    def test_add_skill_from_registry_positive(
        self, fetch_package_mock, split_public_id_mock
    ):
        """Test add from registry positive result."""
        public_id = "owner/name:version"
        obj_type = 'skill'
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--registry", obj_type, public_id],
            standalone_mode=False
        )
        assert result.exit_code == 0
        split_public_id_mock.assert_called_once_with(public_id)
        fetch_package_mock.assert_called_once_with(
            obj_type, public_id=public_id, cwd='.'
        )

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddSkillFailsWhenSkillNotInRegistry:
    """Test that the command 'aea add skill' fails when the skill is not in the registry."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_name = "unknown_skill"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False)
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", cls.skill_name], standalone_mode=False)

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_error_message_skill_already_existing(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find skill: '{skill_name}''
        """
        s = "Cannot find skill: '{}'.".format(self.skill_name)
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddSkillFailsWhenConfigFileIsNotCompliant:
    """Test that the command 'aea add connection' fails when the configuration file is not compliant with the schema."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_name = "echo"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False)
        assert result.exit_code == 0
        os.chdir(cls.agent_name)

        # change default registry path
        config = AgentConfig.from_json(yaml.safe_load(open(DEFAULT_AEA_CONFIG_FILE)))
        config.registry_path = os.path.join(ROOT_DIR, "packages")
        yaml.safe_dump(config.json, open(DEFAULT_AEA_CONFIG_FILE, "w"))

        # change the serialization of the AgentConfig class so to make the parsing to fail.
        cls.patch = unittest.mock.patch.object(aea.configurations.base.SkillConfig, "from_json",
                                               side_effect=ValidationError("test error message"))
        cls.patch.__enter__()

        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", cls.skill_name], standalone_mode=False)

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_configuration_file_not_valid(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find skill: '{skill_name}''
        """
        self.mocked_logger_error.assert_called_once_with("Skill configuration file not valid: test error message")

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        cls.patch.__exit__()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAddSkillFailsWhenDirectoryAlreadyExists:
    """Test that the command 'aea add skill' fails when the destination directory already exists."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_name = "echo"
        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()

        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False)
        assert result.exit_code == 0
        os.chdir(cls.agent_name)

        # change default registry path
        config = AgentConfig.from_json(yaml.safe_load(open(DEFAULT_AEA_CONFIG_FILE)))
        config.registry_path = os.path.join(ROOT_DIR, "packages")
        yaml.safe_dump(config.json, open(DEFAULT_AEA_CONFIG_FILE, "w"))

        Path("skills", cls.skill_name).mkdir(parents=True, exist_ok=True)
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", cls.skill_name], standalone_mode=False)

    def test_exit_code_equal_to_1(self):
        """Test that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_file_exists_error(self):
        """Test that the log error message is fixed.

        The expected message is: 'Cannot find skill: '{skill_name}''
        """
        s = "[Errno 17] File exists: './skills/{}'".format(self.skill_name)
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
