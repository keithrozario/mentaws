import os
from datetime import datetime, timedelta
from argparse import ArgumentParser, Namespace

from mentaws import main
import boto3
import keyring

import pytest

from .settings import platform_config, test_key

# mock client for session token
class MockClient:

    # mock client
    @staticmethod
    def get_session_token(DurationSeconds=3600):
        return {
            "Credentials": {
                "AccessKeyId": "ASIA1234567890",
                "SecretAccessKey": "kWcrlUX5JEDGM/LtmEENI/aVmYvHNif5zB+d9+ct",
                "SessionToken": "kWcrlUX5JEDGM/LtmEENI/aVmYvHNif5zB+d9+ct?<>!@#$",
                "Expiration": datetime.now() + timedelta(seconds=DurationSeconds),
            }
        }


def mock_get_key(*args, **kwargs):
    return test_key


def test_help(monkeypatch):

    """
    Test no commands
    """

    # Run
    monkeypatch.setattr("sys.argv", ["mentaws"])
    command = main.main()
    assert command == "help"

    monkeypatch.setattr("sys.argv", ["mentaws", "help"])
    command = main.main()
    assert command == "help"


def test_other_commands(monkeypatch):

    """
    Test no commands
    """

    # setup
    monkeypatch.setattr("sys.argv", ["mentaws", "setup"])
    command = main.main()
    assert command == "setup"

    # List
    monkeypatch.setattr("sys.argv", ["mentaws", "list"])
    command = main.main()
    assert command == "list"

    # Status
    monkeypatch.setattr("sys.argv", ["mentaws", "status"])
    command = main.main()
    assert command == "status"

    # Status
    monkeypatch.setattr("sys.argv", ["mentaws", "remove"])
    command = main.main()
    assert command == 'fail'

    # # Invalid
    # monkeypatch.setattr("sys.argv", ["mentaws", "invalidCommand"])
    # with pytest.raises(SystemExit) as pytest_wrapped_e:
    #         command = main.main()
    # assert pytest_wrapped_e.type == SystemExit


def test_refresh(monkeypatch):
    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

    def mock_boto3_client(*args, **kwargs):
        if args[0] == "sts":
            return MockClient()

    monkeypatch.setattr(boto3, "client", mock_boto3_client)
    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    # Refresh
    monkeypatch.setattr("sys.argv", ["mentaws", "refresh"])
    command = main.main()
    assert command == "refresh"
