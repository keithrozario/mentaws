from mentaws import main

import pytest
import os

import tests.settings as settings


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
        if os.path.exists(settings.creds_file_path) and os.path.exists(settings.copy_creds_file_path):
            # copy creds
            with open(settings.copy_creds_file_path, "rb") as src, open(
                settings.creds_file_path, "wb"
            ) as dst:
                dst.write(src.read())

    assert os.path.isdir(settings.platform_config["aws_directory"]) == True
    assert os.path.exists(settings.creds_file_path) == True


def test_setup_config_file():

    config_file_copy = os.path.join(os.getcwd(), "tests", "config")

    # copy config to config folder
    with open(config_file_copy, "rb") as src, open(settings.config_file_path, "wb") as dst:
        dst.write(src.read())

    assert os.path.exists(settings.config_file_path) == True


def test_not_yet_setup():

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main.refresh()
    assert pytest_wrapped_e.type == SystemExit

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main.list_profiles()
    assert pytest_wrapped_e.type == SystemExit
