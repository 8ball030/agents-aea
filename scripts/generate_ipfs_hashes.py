#!/usr/bin/env python3
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

"""
This script generates the IPFS hashes for all packages.

This script requires that you have IPFS installed:
- https://docs.ipfs.io/guides/guides/install/
"""

import collections
import csv
import operator
import os
import re
import shutil
import signal
import subprocess  # nosec
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, cast

import ipfshttpclient

import yaml

from aea.configurations.base import (
    AgentConfig,
    ConnectionConfig,
    ProtocolConfig,
    SkillConfig,
    _compute_fingerprint,
    PackageConfiguration,
    ConfigurationType,
    ContractConfig,
    Configuration,
)
from aea.helpers.base import yaml_dump
from aea.helpers.ipfs.base import IPFSHashOnly

AUTHOR = "fetchai"
CORE_PATH = Path("aea")
TEST_PATH = Path("tests") / "data"
PACKAGE_HASHES_PATH = "packages/hashes.csv"
TEST_PACKAGE_HASHES_PATH = "tests/data/hashes.csv"

type_to_class_config = {
    ConfigurationType.AGENT: AgentConfig,
    ConfigurationType.PROTOCOL: ProtocolConfig,
    ConfigurationType.CONNECTION: ConnectionConfig,
    ConfigurationType.SKILL: SkillConfig,
    ConfigurationType.CONTRACT: ContractConfig,
}


def _get_all_packages() -> List[Tuple[ConfigurationType, Path]]:
    """
    Get all the hashable package of the repository.

    In particular, get them from:
    - aea/*
    - packages/*
    - tests/data/*

    :return: pairs of (package-type, path-to-the-package)
    """

    def package_type_and_path(package_path: Path) -> Tuple[ConfigurationType, Path]:
        """Extract the configuration type from the path."""
        item_type_plural = package_path.parent.name
        item_type_singular = item_type_plural[:-1]
        return ConfigurationType(item_type_singular), package_path

    CORE_PACKAGES = list(
        map(
            package_type_and_path,
            [
                CORE_PATH / "protocols" / "default",
                CORE_PATH / "protocols" / "scaffold",
                CORE_PATH / "connections" / "stub",
                CORE_PATH / "connections" / "scaffold",
                CORE_PATH / "contracts" / "scaffold",
                CORE_PATH / "skills" / "error",
                CORE_PATH / "skills" / "scaffold",
            ],
        )
    )

    PACKAGES = list(
        map(
            package_type_and_path,
            filter(operator.methodcaller("is_dir"), Path("packages").glob("*/*/*/")),
        )
    )

    TEST_PACKAGES = [
        (ConfigurationType.AGENT, TEST_PATH / "dummy_aea"),
        (ConfigurationType.CONNECTION, TEST_PATH / "dummy_connection"),
        (ConfigurationType.SKILL, TEST_PATH / "dependencies_skill"),
        (ConfigurationType.SKILL, TEST_PATH / "exception_skill"),
        (ConfigurationType.SKILL, TEST_PATH / "dummy_skill"),
    ]

    ALL_PACKAGES = CORE_PACKAGES + PACKAGES + TEST_PACKAGES
    return ALL_PACKAGES


def sort_configuration_file(config: PackageConfiguration):
    """Sort the order of the fields in the configuration files."""
    # load config file to get ignore patterns, dump again immediately to impose ordering
    configuration_filepath = config.directory / config.default_configuration_filename
    yaml_dump(config.ordered_json, configuration_filepath.open("w"))


def ipfs_hashing(
    client: ipfshttpclient.Client,
    configuration: PackageConfiguration,
    package_type: ConfigurationType,
):
    """
    Hashes a package and its components.

    :param client: a connected IPFS client.
    :param configuration: the package configuration.
    :param package_type: the package type.
    :return: the hash of the whole package.
    """
    print("Processing package {} of type {}".format(configuration.name, package_type))

    # hash again to get outer hash (this time all files):
    # TODO we still need to ignore some files
    #      use ignore patterns somehow
    # ignore_patterns = configuration.fingerprint_ignore_patterns
    result_list = client.add(configuration.directory)
    for result_dict in result_list:
        if configuration.name == result_dict["Name"]:
            key = os.path.join(
                configuration.author, package_type.to_plural(), configuration.name
            )
            package_hashes[key] = result_dict["Hash"]


def to_csv(package_hashes: Dict[str, str], path: str):
    """Outputs a dictionary to CSV."""
    try:
        ordered = collections.OrderedDict(sorted(package_hashes.items()))
        with open(path, "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(ordered.items())
    except IOError:
        print("I/O error")


class IPFSDaemon:
    """
    Set up the IPFS daemon.

    :raises Exception: if IPFS is not installed.
    """

    def __init__(self):
        # check we have ipfs
        res = shutil.which("ipfs")
        if res is None:
            raise Exception("Please install IPFS first!")

    def __enter__(self):
        # run the ipfs daemon
        self.process = subprocess.Popen(  # nosec
            ["ipfs", "daemon"], stdout=subprocess.PIPE, env=os.environ.copy(),
        )
        print("Waiting for the IPFS daemon to be up.")
        time.sleep(5.0)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # terminate the ipfs daemon
        self.process.send_signal(signal.SIGINT)
        self.process.wait(timeout=10)
        poll = self.process.poll()
        if poll is None:
            self.process.terminate()
            self.process.wait(2)


def load_configuration(
    package_type: ConfigurationType, package_path: Path
) -> PackageConfiguration:
    """
    Load a configuration, knowing the type and the path to the package root.

    :param package_type: the package type.
    :param package_path: the path to the package root.
    :return: the configuration object.
    """
    configuration_class = type_to_class_config[package_type]
    configuration_filepath = (
        package_path / configuration_class.default_configuration_filename
    )
    configuration_obj = configuration_class.from_json(
        yaml.safe_load(configuration_filepath.open())
    )
    configuration_obj._directory = package_path
    return cast(PackageConfiguration, configuration_obj)


def assert_hash_consistency(fingerprint, path_prefix) -> None:
    """
    Check that our implementation of IPFS hashing for a package is correct
    against the true IPFS.

    :param fingerprint: the fingerprint dictionary.
    :param path_prefix: the path prefix to prepend.
    :return: None.
    :raises AssertionError: if the IPFS hashes don't match.
    """
    # confirm ipfs only generates same hash:
    for file_name, ipfs_hash in fingerprint.items():
        path = path_prefix / file_name
        ipfsho_hash = ipfs_hash_only.get(str(path))
        assert ipfsho_hash == ipfs_hash, "WARNING, hashes don't match for: {}".format(
            path
        )


def _replace_fingerprint_non_invasive(fingerprint_dict: dict, text: str):
    """
    Replace the fingerprint in a configuration file (not invasive).

    We need this function because libraries like `yaml` may modify the
    content of the .yaml file when loading/dumping. Instead,
    working with the content of the file gives us finer granularity.

    :param text: the content of a configuration file.
    :param fingerprint_dict: the fingerprint dictionary.
    :return:
    """
    to_row = lambda x: x[0] + ": " + x[1]
    replacement = "\nfingerprint:\n  {}\n".format(
        "\n  ".join(map(to_row, sorted(fingerprint_dict.items())))
    )
    return re.sub(r"\nfingerprint:\W*\n(?:\W+.*\n)*", replacement, text)


def update_fingerprint(configuration: PackageConfiguration) -> None:
    """
    Update the fingerprint of a package.

    :param configuration: the configuration object.
    :return: None
    """
    # we don't process agent configurations
    if isinstance(configuration, AgentConfig):
        return
    fingerprint = _compute_fingerprint(
        configuration.directory,
        ignore_patterns=configuration.fingerprint_ignore_patterns,
    )
    assert_hash_consistency(fingerprint, configuration.directory)

    config_filepath = (
        configuration.directory / configuration.default_configuration_filename
    )
    old_content = config_filepath.read_text()
    new_content = _replace_fingerprint_non_invasive(fingerprint, old_content)
    config_filepath.write_text(new_content)


if __name__ == "__main__":
    return_code = 0
    package_hashes = {}  # type: Dict[str, str]
    test_package_hashes = {}  # type: Dict[str, str]
    try:
        # run the ipfs daemon
        with IPFSDaemon():

            # # connect ipfs client
            client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
            ipfs_hash_only = IPFSHashOnly()

            # ipfs hash the packages
            for package_type, package_path in _get_all_packages():
                configuration_obj = load_configuration(package_type, package_path)
                sort_configuration_file(configuration_obj)
                update_fingerprint(configuration_obj)
                ipfs_hashing(client, configuration_obj, package_type)

            # output the package hashes
            to_csv(package_hashes, PACKAGE_HASHES_PATH)
            to_csv(test_package_hashes, TEST_PACKAGE_HASHES_PATH)

            print("Done!")
    except Exception as e:
        return_code = 1
        print(str(e))

    sys.exit(return_code)
