import os
from mentaws import config

platform_config = config.get_platform_config()
test_key = "VlBrGT5dCUh0IHW6WSU8-wdJEJbjCuUhAQ1HZn352Nk="
bad_key = "QUkb3rCxRW4YpybqVa_0SNBGsDDZQ2aOKjXtrrpRS8Y="  # invalid key
num_profiles = 6
profiles = [
    "default",
    "mentaws1",
    "mentaws2",
    "mentaws3",
    "mentawsFail",
    "testassumptionprofile",
]


db_file_path = os.path.join(
    platform_config["aws_directory"], platform_config["database_file"]
)
creds_file_path = os.path.join(
    platform_config["aws_directory"], platform_config["creds_file_name"]
)
copy_creds_file_path = os.path.join(
    platform_config["aws_directory"], f'{platform_config["creds_file_name"]}.copy'
)
config_file_path = os.path.join(
    platform_config["aws_directory"], f'{platform_config["config_file_name"]}'
)
