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

from .settings import platform_config, bad_key, num_profiles, profiles

def mock_get_key(*args, **kwargs):
    return bad_key


def test_setup(monkeypatch):
    """
    Database already setup
    """

    # Run setup    
    profiles = main.setup()
    assert profiles is None


def test_delete_unkown_profile(monkeypatch):

    """
    Test the delete profile command, answering 'yes' when prompted
    """
    response = main.remove('unknownProfile')
    assert response == False


def test_refresh_bad_password(monkeypatch):

    """
    Test the refresh command, with mock AWS Client
    """

    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

  
    monkeypatch.setattr(keyring,"get_password", mock_get_key)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
            main.refresh()
    assert pytest_wrapped_e.type == SystemExit


def test_delete_profile_yes(monkeypatch):

    """
    Test the delete profile command, answering 'yes' when prompted
    """
    global num_profiles
    yes = StringIO('y\n')
    monkeypatch.setattr('sys.stdin', yes)

    profiles_before = main.list_profiles()
    main.remove('noProfileWithThisName')
    profiles_after = main.list_profiles()

    assert len(profiles_before) == len(profiles_after)