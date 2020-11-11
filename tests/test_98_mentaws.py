"""
Real refresh with real AWS credentials against the real api (no mocking, or monkeypatching)
"""

import os
from datetime import datetime

import keyring
import boto3

from mentaws import main

from tests.settings import platform_config, test_key, profiles

from click.testing import CliRunner
import pytest

def mock_get_key(*args, **kwargs):
    return test_key

@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_refresh(runner, monkeypatch):

    """
    Test the refresh command, with **real** AWS Client, (real call to AWS)
    """

    creds_path = os.path.join(
        platform_config["aws_directory"], platform_config["creds_file_name"]
    )

    monkeypatch.setattr(keyring, "get_password", mock_get_key)

    result = runner.invoke(main.main, ['refresh','-p','default,mentaws1,mentaws2,mentawsFail'])
    assert result.exit_code == 0

    file_stat = os.stat(creds_path)
    file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
    assert file_age.total_seconds() < 2

    for profile in ["default", "mentaws1", "mentaws2"]:
        mentaws_session = boto3.session.Session(profile_name=profile)
        sts_client = mentaws_session.client("sts")
        response = sts_client.get_caller_identity()
        assert response["Account"] == "880797093042"
