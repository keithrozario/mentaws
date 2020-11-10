import os
import filecmp

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
    assert filecmp.cmp(settings.creds_file_path,settings.copy_creds_file_path,shallow=False) == True

