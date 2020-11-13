from mentaws import __version__
from mentaws import config
from mentaws import operations

import os
import pytest
import subprocess
from configparser import ConfigParser
from io import StringIO
from datetime import datetime, timedelta

import boto3
import keyring

from tests.settings import platform_config, test_key, num_profiles, profiles

import pytest

def mock_get_key(*args, **kwargs):
    return test_key


def mock_set_key(*args, **kwargs):
    return


def test_version():
    assert __version__ == "0.6.0"


def test_setup(monkeypatch):
    """
    Test the setup command
    """

    monkeypatch.setattr(keyring, "set_password", mock_set_key)
    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    # Run setup
    operations.setup_new_db()

    db_path = os.path.join(
        platform_config["aws_directory"], platform_config["database_file"]
    )

    assert os.path.exists(db_path) == True


def test_list_profiles_in_db():

    db_profiles = operations.list_profiles_in_db()
    assert db_profiles.sort() == profiles.sort()

def test_check_profile_in_db():

    for profile in profiles:
        assert operations.check_profile_in_db(profile) is True


def test_get_plaintext_credentials(monkeypatch):

    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    creds = operations.get_plaintext_credentials(all=True)
    assert len(creds) == len(profiles)
    for cred in creds:
        if cred['profile'] == 'testassumptionprofile':
            assert cred['role_arn'] == "arn:aws:iam::123456789012:role/testing"
            assert cred['source_profile'] == 'default'
            assert cred['role_session_name'] == 'OPTIONAL_SESSION_NAME'

    creds = operations.get_plaintext_credentials()
    assert len(creds) == len(profiles)-1
    for cred in creds:
        assert cred["aws_access_key_id"][:4] == "AKIA"

    creds = operations.get_plaintext_credentials("mentaws1,default")
    assert len(creds) == 2


def test_remove_profile_from_db():

    operations.remove_profile_from_db('mentawsFail')
    db_profiles = operations.list_profiles_in_db()
    assert 'mentawsFail' not in db_profiles
