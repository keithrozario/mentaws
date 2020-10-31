from sementara import __version__
from sementara import main, operations, aws_operations

import os
import pytest
import getpass
import subprocess
from datetime import datetime, timedelta

import boto3

real_password = "aA65M&c7&jU6S1PYGjkcV"
new_password = "Cz09^PWHmWVvT5TB*vM8V"
wrong_password = "password"
platform_config = operations.get_platform_config()

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

# xfail is an optional fail.
@pytest.mark.xfail(raises=subprocess.CalledProcessError)
def test_initialize():
    reset_script = os.path.join(
        platform_config["aws_directory"], 'reset.sh'
    )
    
    # undo previous setup
    return_value = subprocess.run([reset_script], check=True, cwd=platform_config["aws_directory"])

def test_version():
    assert __version__ == '0.4.3'

# setup with not matching passwords
def test_setup_wrong_password(monkeypatch):

    def mock_password(**kwargs):
        if kwargs['prompt'] == "🔑 Confirm Password: ":
            return wrong_password
        return real_password
    
    monkeypatch.setattr(getpass, "getpass", mock_password)
    
    with pytest.raises(SystemExit) as pytest_wrapped_e:
            main.setup()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

# setup
def test_setup(monkeypatch):

    def mock_password(**kwargs):
        return real_password
    
    monkeypatch.setattr(getpass, "getpass", mock_password)
    conf_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["conf_file_name"]
    )
    enc_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["encrypted_file_name"]
    )
    profile_file_path = os.path.join(
        platform_config["aws_directory"], platform_config["profile_file_name"]
    )


    # Run setup    
    main.setup()
   
    assert os.path.exists(conf_file_path) == True
    assert os.path.exists(enc_file_path) == True
    assert os.path.exists(profile_file_path) == True
    

# refresh with good password
def test_refresh_mock(monkeypatch):

    def mock_password(**kwargs):
        return real_password
    
    def mock_boto3_client(*args, **kwargs):
        if args[0] == 'sts':
            return MockClient()

    monkeypatch.setattr(getpass, "getpass", mock_password)
    monkeypatch.setattr(boto3,"client", mock_boto3_client)
    main.refresh()

# refresh with wrong password
def test_refresh_wrong_password(monkeypatch):

    def mock_password(**kwargs):
        return wrong_password
    monkeypatch.setattr(getpass, "getpass", mock_password)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
            main.refresh()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

# Mismatch passwords
def test_reencrypt_mismatch_passwords(monkeypatch):

    def mock_password(**kwargs):
        if kwargs['prompt'] == "🔑 Enter **current** password: ":
            password = real_password
        if kwargs['prompt'] == "🔑 Enter **NEW** password: ":
            password = real_password
        if kwargs['prompt'] == "🔑 Confirm **NEW** password: ":
            password = new_password
        return password
    
    monkeypatch.setattr(getpass, "getpass", mock_password)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
             main.reencrypt()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

# Reencrypt
def test_reencrypt(monkeypatch):

    def mock_password(**kwargs):
        if kwargs['prompt'] == "🔑 Enter **current** password: ":
            password = real_password
        elif kwargs['prompt'] == "🔑 Enter **NEW** password: ":
            password = new_password
        elif kwargs['prompt'] == "🔑 Confirm **NEW** password: ":
            password = new_password
        elif kwargs['prompt'] == "🔑 Enter password: ":
            password = new_password

        return password
    
    def mock_boto3_client(*args, **kwargs):
        if args[0] == 'sts':
            return MockClient()
    
    # set back to original password
    def mock_password_set_back(**kwargs):
        if kwargs['prompt'] == "🔑 Enter **current** password: ":
            password = new_password
        elif kwargs['prompt'] == "🔑 Enter **NEW** password: ":
            password = real_password
        elif kwargs['prompt'] == "🔑 Confirm **NEW** password: ":
            password = real_password

        return password

    monkeypatch.setattr(getpass, "getpass", mock_password)
    monkeypatch.setattr(boto3,"client", mock_boto3_client)

    # reencrypt with new password
    main.reencrypt()
    main.refresh()
    # refresh with new password
    monkeypatch.setattr(getpass, "getpass", mock_password_set_back)
    main.reencrypt()

    return


# refresh with good password
def test_refresh(monkeypatch):

    def mock_password(**kwargs):
        return real_password
    
    monkeypatch.setattr(getpass, "getpass", mock_password)
    main.refresh()

def test_list_profiles(monkeypatch):

    def mock_password(**kwargs):
        return real_password
    
    monkeypatch.setattr(getpass, "getpass", mock_password)

    profiles = main.list_profiles()
    assert profiles['num_profiles'] == 6
    assert 'LambdaCache' in profiles['profiles']


    profiles = main.remove('LambdaCache')
    assert profiles['num_profiles'] == 5
    assert 'LambdaCache' not in profiles['profiles']


    

