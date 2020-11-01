import platform
from configparser import ConfigParser
import getpass
import secrets
import base64
import json
import os

import sqlite3

from .config import get_platform_config
from .cryptographic_operations import setup_key, encrypt, decrypt

from .exceptions import InvalidPasswordError

from typing import List


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
        conn = sqlite3.connect(sementara_db_path)
        db = conn.cursor()
        db.execute(f'DROP TABLE IF EXISTS {table_name}')
        db.execute(f'CREATE TABLE {table_name} (profile text PRIMARY KEY, \
                                    aws_access_key_id text NOT NULL, \
                                    aws_secret_access_key text NOT NULL \
                                    )')
        conn.commit()
        conn.close()

        # setup encryption key
        setup_key(app_name, key_name)

        # Read credentials from existing file
        creds = ConfigParser()
        with open(creds_file_path, 'r') as creds_file:
            creds.read_string(creds_file.read())
        
        # Write out to database
        write_creds_to_db(creds)

    else:
        print(f"Sementara already setup")

    return True


def list_profiles_in_db(print_profiles: bool=True) -> List[str]:
    """
    List all profiles in database
    """
    conn = sqlite3.connect(sementara_db_path)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    db.execute(f'SELECT profile FROM {table_name}')

    print("\n")
    profiles = list()
    for k, row in enumerate(db):
        profiles.append(row['profile'])
        if print_profiles:
            print(f"{k+1:2}. {row['profile']}")

    if print_profiles:
        print(f"\nFound total of {k+1} profiles 👷🏿 in database\n")
    
    conn.close()

    return profiles

def get_plaintext_credentials(profiles: List[str]=[]) -> List[dict]:

    creds = list()

    if len(profiles) == 0:
        conn = sqlite3.connect(sementara_db_path)
        conn.row_factory = sqlite3.Row
        db = conn.cursor()
        db.execute(f'SELECT * FROM {table_name}')

    
    for row in db:
        temp_row = dict()
        for key in row.keys():
            if key == 'aws_secret_access_key':
                temp_row[key] = decrypt(
                    encrypted_string=row[key],
                    app_name=app_name,
                    key_name=key_name
                )
            else:
                temp_row[key] = row[key]
        creds.append(temp_row)

    return creds


def write_creds_file(config: ConfigParser):
    
    with open(creds_file_path, "w") as creds_file:
        config.write(creds_file)

    return


def check_new_profiles() -> dict:

    creds = ConfigParser()
    creds.read(filenames=[creds_file_path], encoding='utf-8')
    existing_profiles = list_profiles_in_db(print_profiles=False)

    new_profiles = dict()
    for section in creds.sections():
        key_id = creds.get(section, "aws_access_key_id")
        if key_id[:4] == "AKIA" and section not in existing_profiles:
            new_section = {}
            for option in creds.options(section):
                new_section[option] = creds.get(section, option)
            new_profiles[section] = new_section
    
    # Write new profiles to database
    if len(new_profiles.keys()) > 0:
        print(f"Found {len(new_profiles.keys())} new profiles👷🏿 in credentials file...adding to DB")
        new_creds = ConfigParser()
        new_creds.read_dict(new_profiles)
        write_creds_to_db(new_creds)

    return new_profiles


def write_creds_to_db(creds: ConfigParser) -> bool:

    conn = sqlite3.connect(sementara_db_path)
    db = conn.cursor()
    
    for k, section in enumerate(creds.sections()):
        profile = section
        aws_access_key_id = creds.get(section, 'aws_access_key_id')
        
        # Encrypt secret key
        aws_secret_access_key = encrypt(
            plaintext=creds.get(section, 'aws_secret_access_key'),
            app_name=app_name,
            key_name=key_name
        )

        db.execute(
            f'INSERT INTO {table_name} (profile, aws_access_key_id, aws_secret_access_key) VALUES(?,?,?)',
            (profile, aws_access_key_id, aws_secret_access_key)
        )
        print(f"{profile:25} profile loaded into database")
    
    print(f"\nLoaded {k+1} new profiles into sementara 👷🏿\n\n")
    conn.commit()
    conn.close()

    return True


def remove_profile_from_db(profile_name: str) -> bool:

    conn = sqlite3.connect(sementara_db_path)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    db.execute(f'SELECT profile FROM {table_name} WHERE profile=?', (profile_name,))

    try:
        row = [item for item in db]
        print(f"This action will delete the 👷🏿{row[0]['profile']}👷🏿 profile from sementara permanently.")
        if yes_or_no("Are you sure you want to proceed"):
            db.execute(f"DELETE FROM {table_name} WHERE profile = ?", (profile_name,))
            conn.commit()
        else:
            print(f"Cancelled Operation, {row[0]['profile']} was NOT deleted")
            
    except (IndexError, KeyError):
        print(f"No such profile found")

    conn.close()
    return True

def yes_or_no(question):
    reply = str(input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    else:
        return False