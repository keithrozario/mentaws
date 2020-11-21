import os
from datetime import datetime, timedelta
from configparser import ConfigParser

from mentaws import main, operations
from mentaws import config as mentaws_config
import boto3
import keyring

from click.testing import CliRunner
import pytest

from tests.settings import platform_config, test_key
import tests.settings as settings

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


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_delete_old_files():

    try:
        os.remove(settings.db_file_path)
    except FileNotFoundError:
        pass

    assert os.path.exists(settings.db_file_path) == False


def test_setup_creds_file():
    """
    Loading credentials and credentials.copy file into environment if one doesn't exists.
    We use the CREDENTIALS_FILE_CONTENTS envar via GitHub Actions for our pipelin
    """

    try:
        os.mkdir(path=settings.platform_config["aws_directory"], mode=0o755)
        with open(settings.creds_file_path, "w") as cred_file:
            cred_file.write(os.environ.get("CREDENTIALS_FILE_CONTENTS", ""))
        with open(f"{settings.creds_file_path}.copy", "w") as cred_file:
            cred_file.write(os.environ.get("CREDENTIALS_FILE_CONTENTS", ""))
        print("Loaded creds file")
    except FileExistsError:
        # testing on local machine
        if os.path.exists(settings.creds_file_path) and os.path.exists(
            settings.copy_creds_file_path
        ):
            # copy creds
            with open(settings.copy_creds_file_path, "rb") as src, open(
                settings.creds_file_path, "wb"
            ) as dst:
                dst.write(src.read())

    assert os.path.isdir(settings.platform_config["aws_directory"]) == True
    assert os.path.exists(settings.creds_file_path) == True


def test_hello(runner):
    result = runner.invoke(main.main)
    assert result.exit_code == 0
    assert result.output[:6] == "Usage:"

    result = runner.invoke(main.main, ["--help"])
    assert result.exit_code == 0
    assert result.output[:6] == "Usage:"


def test_setup(runner, monkeypatch):

    monkeypatch.setattr(keyring, "get_password", mock_get_key)
    monkeypatch.setattr(keyring, "set_password", mock_get_key)

    result = runner.invoke(main.main, ["setup"])
    assert result.exit_code == 0
    assert mentaws_config.setup_message in result.output

    result = runner.invoke(main.main, ["setup"])
    assert result.exit_code == 0
    assert mentaws_config.already_setup_message in result.output


def test_refresh(runner, monkeypatch):

    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

    def mock_boto3_client(*args, **kwargs):
        if args[0] == "sts":
            return MockClient()

    monkeypatch.setattr(boto3, "client", mock_boto3_client)
    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    result = runner.invoke(main.main, ["refresh"])
    assert result.exit_code == 0
    assert mentaws_config.refresh_message in result.output

    result = runner.invoke(main.main, ["refresh", "-p", "default"])
    assert result.exit_code == 0
    assert mentaws_config.refresh_message in result.output

    result = runner.invoke(main.main, ["refresh", "-p", "mentaws3,default"])
    assert result.exit_code == 0
    assert mentaws_config.refresh_message in result.output

    file_stat = os.stat(creds_path)
    file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
    assert file_age.total_seconds() < 2


def test_status(runner):

    result = runner.invoke(main.main, ["status"])
    assert result.exit_code == 0
    assert "👷🏿 Profile" in result.output


def test_remove_profile(runner):

    result = runner.invoke(main.main, ["remove", "-p", "mentaws1", "--yes"])
    assert result.exit_code == 0
    assert operations.check_profile_in_db("mentaws1") is False


def test_add_new_profile(runner, monkeypatch):
    def mock_boto3_client(*args, **kwargs):
        if args[0] == "sts":
            return MockClient()

    monkeypatch.setattr(boto3, "client", mock_boto3_client)
    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    # copy over deleted profile from .copy file back into original credentails file
    config = ConfigParser()
    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )
    config.read([creds_path, f"{creds_path}.copy"])

    # remove extra fields
    config.remove_option("mentaws1", "aws_session_token")
    config.remove_option("mentaws1", "aws_token_expiry_time_human")
    config.remove_option("mentaws1", "aws_token_expiry_time_machine")

    with open(creds_path, "w") as creds_file:
        config.write(creds_file)

    result = runner.invoke(main.main, ["refresh", "-p", "default"])
    assert result.exit_code == 0
    assert operations.check_profile_in_db("mentaws1") is True

    result = runner.invoke(main.main, ["refresh"])


def test_refresh_some_profiles(runner, monkeypatch):
    """
    Test refreshing only some profiles
    """
    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

    def mock_boto3_client(*args, **kwargs):
        if args[0] == "sts":
            return MockClient_2()

    monkeypatch.setattr(boto3, "client", mock_boto3_client)
    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    result = runner.invoke(main.main, ["refresh", "-p", "mentaws1,mentaws2"])
    assert result.exit_code == 0

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


def test_unsetup(runner):
    """
    Unsetup is tested in test_99_unsetup
    """
    pass
