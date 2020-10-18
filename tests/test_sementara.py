from sementara import __version__
from sementara import main, operations
import os
import pytest
import getpass
import subprocess

real_password = "aA65M&c7&jU6S1PYGjkcV"
wrong_password = "password"
platform_config = operations.get_platform_config()

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

# # setup with not matching passwords
# def test_setup_wrong_password(monkeypatch):

#     def mock_password(**kwargs):
#         if kwargs['prompt'] == "🔑 Confirm Password: ":
#             return wrong_password
#         return real_password
    
#     monkeypatch.setattr(getpass, "getpass", mock_password)
    
#     with pytest.raises(SystemExit) as pytest_wrapped_e:
#             main.setup()
#     assert pytest_wrapped_e.type == SystemExit
#     assert pytest_wrapped_e.value.code == 1

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
    

# # refresh with good password
# def test_refresh(monkeypatch):

#     def mock_password(**kwargs):
#         return real_password
    
#     monkeypatch.setattr(getpass, "getpass", mock_password)
#     main.refresh()

# # refresh with wrong password
# def test_refresh(monkeypatch):

#     def mock_password(**kwargs):
#         return wrong_password
#     monkeypatch.setattr(getpass, "getpass", mock_password)

#     with pytest.raises(SystemExit) as pytest_wrapped_e:
#             main.refresh()
#     assert pytest_wrapped_e.type == SystemExit
#     assert pytest_wrapped_e.value.code == 1
    

