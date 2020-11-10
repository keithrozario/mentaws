import os
import configparser

import keyring

import tests.settings as settings

from mentaws import main

def mock_get_key(*args, **kwargs):
    return settings.test_key


def test_unsetup(monkeypatch):
    """
    Test unsetup
    """
    
    monkeypatch.setattr(keyring, "get_password", mock_get_key)
    
    # unsetup
    monkeypatch.setattr("sys.argv", ["mentaws", "unsetup"])
    command = main.main()
    assert command == "unsetup"
    
    assert os.path.isdir(settings.platform_config["aws_directory"]) == True
    assert os.path.exists(settings.creds_file_path) == True
    assert os.path.exists(settings.db_file_path) == False

def test_file_comparison():

    new_config = configparser.ConfigParser()
    new_config.read(settings.creds_file_path)

    old_config = configparser.ConfigParser()
    old_config.read(settings.copy_creds_file_path)

    for section in old_config.sections():
        for option in old_config.options(section):
            assert old_config.get(section,option) == new_config.get(section, option)

    for section in new_config.sections():
        for option in new_config.options(section):
            assert old_config.get(section,option) == new_config.get(section, option)
