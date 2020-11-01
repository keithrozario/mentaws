import platform
from configparser import ConfigParser
import getpass
import secrets
import base64
import json
import os

import records

from .config import get_platform_config
from .cryptographic_operations import setup_key, encrypt

from .exceptions import InvalidPasswordError


# General configuration
config = get_platform_config()
table_name = config['default_table_name']
app_name = config['default_app_name']
key_name = config['encryption_key_name']

sementara_db_path = os.path.join(
    config["aws_directory"], config["database_file"]
)
creds_file_path = os.path.join(
    config["aws_directory"], config["creds_file_name"]
)


def setup_new_db() -> bool:
    """
    Creates a new sqlite database, and populates it with the credentials from the creds file
    """

    if not os.path.isfile(sementara_db_path):

        # Create database
        db = records.Database(f'sqlite:////{sementara_db_path}')
        db.query(f'DROP TABLE IF EXISTS {table_name}')
        db.query(f'CREATE TABLE {table_name} (profile text PRIMARY KEY, \
                                              aws_access_key_id text NOT NULL, \
                                              aws_secret_access_key text NOT NULL \
                                            )')

        # setup encryption key
        setup_key(app_name, key_name)

        # Read credentials from existing file
        creds = ConfigParser()
        with open(creds_file_path, 'r') as creds_file:
            creds.read_string(creds_file.read())
        
        # Write out to database
        for k, section in enumerate(creds.sections()):
            profile = section
            aws_access_key_id = creds.get(section, 'aws_access_key_id')
            
            # Encrypt secret key
            aws_secret_access_key = encrypt(
                plaintext=creds.get(section, 'aws_secret_access_key'),
                app_name=app_name,
                key_name=key_name
            )

            db.query(
                f'INSERT INTO {table_name} (profile, aws_access_key_id, aws_secret_access_key) VALUES(:profile, :aws_access_key_id, :aws_secret_access_key)',
                profile=profile, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key
            )
            print(f"{profile:25} profile loaded into database")

        print(f"\nLoaded {k} profiles into sementara 👷🏿")
    else:

        print(f"Sementara already setup")

    return True



def check_new_profiles() -> dict:
    platform_config = get_platform_config()

    cred_file_path = os.path.join(platform_config["aws_directory"], "credentials")
    creds = ConfigParser()
    creds.read(filenames=[cred_file_path], encoding='utf-8')

    new_profiles = dict()
    for section in creds.sections():
        key_id = creds.get(section, "aws_access_key_id")
        if key_id[:4] == "AKIA":
            new_section = {}
            for option in creds.options(section):
                new_section[option] = creds.get(section, option)
            new_profiles[section] = new_section

    return new_profiles
