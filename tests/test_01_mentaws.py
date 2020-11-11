from mentaws import __version__
from mentaws import main, config, aws_operations
from configparser import ConfigParser

import os
import pytest
import subprocess
from datetime import datetime, timedelta

import boto3
import keyring
from io import StringIO

from .settings import platform_config, test_key, num_profiles, profiles

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


# mock client for session token
class MockClient_2:

    # mock client
    @staticmethod
    def get_session_token(DurationSeconds=3600):
        return {
            "Credentials": {
                "AccessKeyId": "ASIA999999999",
                "SecretAccessKey": "kWcrlUX5JEDGM/LtmEENI/aVmYvHNif5zB+d9+ct",
                "SessionToken": "kWcrlUX5JEDGM/LtmEENI/aVmYvHNif5zB+d9+ct?<>!@#$",
                "Expiration": datetime.now() + timedelta(seconds=DurationSeconds),
            }
        }


def mock_get_key(*args, **kwargs):
    return test_key


def mock_set_key(*args, **kwargs):
    return


def test_version():
    assert __version__ == "0.5.3"


def test_setup(monkeypatch):

    """
    Test the setup command
    """

    monkeypatch.setattr(keyring, "set_password", mock_set_key)
    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    # Run setup
    profiles = main.setup()
    db_path = os.path.join(
        platform_config["aws_directory"], platform_config["database_file"]
    )

    assert os.path.exists(db_path) == True
    assert len(profiles) > 0


def test_refresh_mock(monkeypatch):

    """
    Test the refresh command, with mock AWS Client
    """

    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

    def mock_boto3_client(*args, **kwargs):
        if args[0] == "sts":
            return MockClient()

    monkeypatch.setattr(boto3, "client", mock_boto3_client)
    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    main.refresh()

    file_stat = os.stat(creds_path)
    file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
    assert file_age.total_seconds() < 2


def test_status():

    statuses = main.status()
    for status in statuses:
        if status["profile"] not in ["testassumptionprofile"]:
            assert status["aws_access_key_id"] == "ASIA1234567890"


def test_list_profiles(monkeypatch):

    """
    Test the list profiles command
    """

    no = StringIO("n\n")
    monkeypatch.setattr("sys.stdin", no)

    profiles = main.list_profiles()
    assert len(profiles) == num_profiles
    assert "mentaws1" in profiles

    main.remove("mentaws1")
    profiles = main.list_profiles()
    assert len(profiles) == num_profiles
    assert "mentaws1" in profiles


def test_delete_profile_yes(monkeypatch):

    """
    Test the delete profile command, answering 'yes' when prompted
    """
    global num_profiles
    yes = StringIO("y\n")
    monkeypatch.setattr("sys.stdin", yes)

    main.remove("mentaws1")
    profiles = main.list_profiles()

    num_profiles -= 1
    assert len(profiles) == num_profiles
    assert "mentaws1" not in profiles


def test_add_profiles(monkeypatch):

    """
    Test the adding profile
     - checks credentials file for any long lived token (AKIA...)
    """

    global num_profiles

    # copy over deleted profile from .copy file back into original credentails file
    config = ConfigParser()
    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )
    config.read([creds_path, f"{creds_path}.copy"])

    # remove extra fields
    config.remove_option('mentaws1', 'aws_session_token')
    config.remove_option('mentaws1', 'aws_token_expiry_time_human')
    config.remove_option('mentaws1', 'aws_token_expiry_time_machine')

    with open(creds_path, "w") as creds_file:
        config.write(creds_file)

    def mock_boto3_client(*args, **kwargs):
        if args[0] == "sts":
            return MockClient()

    monkeypatch.setattr(boto3, "client", mock_boto3_client)
    monkeypatch.setattr(keyring, "set_password", mock_set_key)
    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    profiles = main.list_profiles()
    assert len(profiles) == num_profiles
    assert "mentaws1" not in profiles

    main.refresh()
    profiles = main.list_profiles()
    num_profiles += 1
    assert len(profiles) == num_profiles
    assert "mentaws1" in profiles


def test_refresh_some_profiles(monkeypatch):
    """
    Test refreshing only some profiles
    """
    global profiles
    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

    def mock_boto3_client(*args, **kwargs):
        if args[0] == "sts":
            return MockClient_2()

    monkeypatch.setattr(boto3, "client", mock_boto3_client)
    monkeypatch.setattr(keyring, "set_password", mock_set_key)
    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    main.refresh("mentaws1,mentaws2")

    file_stat = os.stat(creds_path)
    file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
    assert file_age.total_seconds() < 0.5

    new_creds = ConfigParser()
    new_creds.read(filenames=[creds_path])

    # for profile in profiles:
    #     assert profile in new_creds.sections()

    assert new_creds["mentaws1"]["aws_access_key_id"] == "ASIA999999999"
    assert new_creds["mentaws2"]["aws_access_key_id"] == "ASIA999999999"
    assert new_creds["mentaws3"]["aws_access_key_id"] == "ASIA1234567890"
    assert new_creds["default"]["aws_access_key_id"] == "ASIA1234567890"


def test_region_setting():

    assert aws_operations.get_region("default") == "ap-southeast-1"
    assert aws_operations.get_region("mentaws1") == "ap-southeast-1"
    assert aws_operations.get_region("mentaws2") == "ap-southeast-2"
    assert aws_operations.get_region("mentaws3") == "ap-southeast-1"


def test_refresh(monkeypatch):
    """
    Test the refresh command, with **real** AWS Client, (real call to AWS)
    """

    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

    monkeypatch.setattr(keyring, "set_password", mock_set_key)
    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    main.refresh()

    file_stat = os.stat(creds_path)
    file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
    assert file_age.total_seconds() < 2

    for profile in profiles:
        if not profile == "mentawsFail":
            mentaws_session = boto3.session.Session(profile_name=profile)
            sts_client = mentaws_session.client("sts")
            response = sts_client.get_caller_identity()
            assert response["Account"] == "880797093042"
