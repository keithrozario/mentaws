from mentaws import main

import pytest
import os

from .settings import platform_config, test_key, num_profiles, profiles


def test_delete_old_files():

    db_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["database_file"]
    )
    try:
        os.remove(db_file_path)
    except FileNotFoundError:
        pass

    assert os.path.exists(db_file_path) == False


def test_setup_creds_file():
    """
    Loading credentials and credentials.copy file into environment if one doesn't exists.
    We use the CREDENTIALS_FILE_CONTENTS envar via GitHub Actions for our pipelin
    """

    creds_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )
    copy_creds_file_path = os.path.join(
        platform_config["aws_directory"], f'{platform_config["creds_file_name"]}.copy'
    )

    try:
        os.mkdir(path=platform_config["aws_directory"], mode=0o755)
        with open(creds_file_path, "w") as cred_file:
            cred_file.write(os.environ.get("CREDENTIALS_FILE_CONTENTS", ""))
        with open(f"{creds_file_path}.copy", "w") as cred_file:
            cred_file.write(os.environ.get("CREDENTIALS_FILE_CONTENTS", ""))
        print("Loaded creds file")
    except FileExistsError:
        # testing on local machine
        if os.path.exists(creds_file_path) and os.path.exists(copy_creds_file_path):
            # copy creds
            with open(copy_creds_file_path, "rb") as src, open(
                creds_file_path, "wb"
            ) as dst:
                dst.write(src.read())

    assert os.path.isdir(platform_config["aws_directory"]) == True
    assert os.path.exists(creds_file_path) == True


def test_setup_config_file():

    config_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["config_file_name"]
    )
    config_file_copy = os.path.join(os.getcwd(), "tests", "config")

    # copy config to config folder
    with open(config_file_copy, "rb") as src, open(config_file_path, "wb") as dst:
        dst.write(src.read())

    assert os.path.exists(config_file_path) == True


def test_not_yet_setup():

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main.refresh()
    assert pytest_wrapped_e.type == SystemExit

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main.list_profiles()
    assert pytest_wrapped_e.type == SystemExit
