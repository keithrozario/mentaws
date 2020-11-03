from mentaws import __version__
from mentaws import main, config
from configparser import ConfigParser

import os
import pytest
import subprocess
from datetime import datetime, timedelta

import boto3
import keyring
from io import StringIO

platform_config = config.get_platform_config()
test_key = "VlBrGT5dCUh0IHW6WSU8-wdJEJbjCuUhAQ1HZn352Nk="

# mock client for session token
class MockClient:

    # mock client
    @staticmethod
    def get_session_token(DurationSeconds=3600):
        return {
            'Credentials': {
            'AccessKeyId': 'ASIA1234567890',
            'SecretAccessKey': 'kWcrlUX5JEDGM/LtmEENI/aVmYvHNif5zB+d9+ct',
            'SessionToken': 'kWcrlUX5JEDGM/LtmEENI/aVmYvHNif5zB+d9+ct?<>!@#$',
            'Expiration': datetime.now() + timedelta(seconds=DurationSeconds)
            }
        }


def mock_get_key(*args, **kwargs):
    return test_key


def mock_set_key(*args, **kwargs):
    return 
        

## THIS IS ONLY NEEDED WHEN TESTING AGAINST MY LOCAL...
# # xfail is an optional fail.
# @pytest.mark.xfail(raises=subprocess.CalledProcessError)
# def test_initialize():
#     reset_script = os.path.join(
#         platform_config["aws_directory"], 'reset.sh'
#     )
    
#     # undo previous setup
#     return_value = subprocess.run([reset_script], check=True, cwd=platform_config["aws_directory"])


def test_version():
    assert __version__ == '0.4.4'


# setup
def test_setup(monkeypatch):

    monkeypatch.setattr(keyring,"set_password", mock_set_key)
    monkeypatch.setattr(keyring,"get_password", mock_get_key)

    # Run setup    
    profiles = main.setup()
    db_path = os.path.join(
        platform_config["aws_directory"], platform_config["database_file"]
    )

    assert os.path.exists(db_path) == True
    assert len(profiles) > 0


def test_refresh_mock(monkeypatch):

    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

    def mock_boto3_client(*args, **kwargs):
        if args[0] == 'sts':
            return MockClient()
    
    monkeypatch.setattr(boto3,"client", mock_boto3_client)
    monkeypatch.setattr(keyring,"set_password", mock_set_key)
    monkeypatch.setattr(keyring,"get_password", mock_get_key)

    main.refresh()

    file_stat = os.stat(creds_path)
    file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
    assert file_age.seconds < 2


def test_list_profiles_no(monkeypatch):
    
    no = StringIO('n\n')
    monkeypatch.setattr('sys.stdin', no)

    profiles = main.list_profiles()
    assert len(profiles) == 4
    assert 'mentaws1' in profiles

    profiles = main.remove('mentaws1')
    assert len(profiles) == 4
    assert 'mentaws1' in profiles


def test_list_profiles(monkeypatch):
    
    yes = StringIO('y\n')
    monkeypatch.setattr('sys.stdin', yes)

    profiles = main.list_profiles()
    assert len(profiles) == 4
    assert 'mentaws1' in profiles

    main.remove('mentaws1')
    profiles = main.list_profiles()
    assert len(profiles) == 3
    assert 'mentaws1' not in profiles


def test_refresh(monkeypatch):
    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

    monkeypatch.setattr(keyring,"set_password", mock_set_key)
    monkeypatch.setattr(keyring,"get_password", mock_get_key)

    main.refresh()

    file_stat = os.stat(creds_path)
    file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
    assert file_age.seconds < 10


def test_profiles(monkeypatch):

    config = ConfigParser()
    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )
    config.read([creds_path, f"{creds_path}.copy"])
    with open(creds_path, 'w') as creds_file:
        config.write(creds_file)

    monkeypatch.setattr(keyring,"set_password", mock_set_key)
    monkeypatch.setattr(keyring,"get_password", mock_get_key)

    profiles = main.list_profiles()
    assert len(profiles) == 3
    assert 'mentaws1' not in profiles

    main.refresh()
    profiles = main.list_profiles()
    assert len(profiles) == 4
    assert 'mentaws1' in profiles

