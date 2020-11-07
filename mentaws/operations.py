from configparser import ConfigParser, NoOptionError
import json
import os

import sqlite3

from .config import get_platform_config
from .cryptographic_operations import setup_key, encrypt, decrypt

from typing import List


# General configuration
config = get_platform_config()
table_name = config["default_table_name"]
app_name = config["default_app_name"]
key_name = config["encryption_key_name"]

sementara_db_path = os.path.join(config["aws_directory"], config["database_file"])
creds_file_path = os.path.join(config["aws_directory"], config["creds_file_name"])


def setup_new_db() -> List[str]:
    """
    Creates a new sqlite database, and populates it with the credentials from the creds file
    """

    if not os.path.isfile(sementara_db_path):

        # Create database
        conn = sqlite3.connect(sementara_db_path)
        db = conn.cursor()
        db.execute(f"DROP TABLE IF EXISTS {table_name}")
        db.execute(
            f"CREATE TABLE {table_name} (profile text PRIMARY KEY, \
                                    aws_access_key_id text NOT NULL, \
                                    aws_secret_access_key text NOT NULL, \
                                    other_options text \
                                    )"
        )
        conn.commit()
        conn.close()

        # setup encryption key
        setup_key(app_name, key_name)

        # Read credentials from existing file
        creds = ConfigParser()
        with open(creds_file_path, "r") as creds_file:
            creds.read_string(creds_file.read())

        # Write out to database
        profiles = write_creds_to_db(creds)
    else:
        profiles = None

    return profiles


def list_profiles_in_db(print_profiles: bool = True) -> List[str]:
    """
    List all profiles in database
    """
    conn = sqlite3.connect(sementara_db_path)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    db.execute(f"SELECT profile FROM {table_name}")

    profiles = [row["profile"] for row in db]

    conn.close()

    return profiles


def get_plaintext_credentials(profiles: str = "") -> List[dict]:
    """
    Args:
      profiles: comma separated string of aws_profiles to retrieve
    return:
      creds = List of dicts, each with keys (profile, aws_access_key_id, aws_secret_access_key)
    """

    creds = list()
    conn = sqlite3.connect(sementara_db_path)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()

    if len(profiles) == 0:
        db.execute(f"SELECT * FROM {table_name} WHERE aws_access_key_id != ''")
    else:
        profile_list = profiles.split(',')
        # using the ? designator didn't work for me. Let me know if you know how to use this properly
        db.execute(f"SELECT * FROM {table_name} WHERE profile IN {(str(tuple(profile_list)))} AND aws_access_key_id != ''")

    for row in db:
        # Sqlite3 rows are not real dictionaries, do not support easy copying
        temp_row = dict()
        for key in row.keys():
            temp_row[key] = row[key]

        # decrypt secret key here
        temp_row['aws_secret_access_key'] = decrypt(
            encrypted_string=row['aws_secret_access_key'], app_name=app_name, key_name=key_name
        )
        # handle additional fiels
        other_options = json.loads(temp_row['other_options'])
        del temp_row['other_options']
        for key in other_options.keys():
            temp_row[key] = other_options[key]

        creds.append(temp_row)

    return creds


def write_creds_file(config: ConfigParser, replace: bool=True):

    """
    Writes out data in config to credentials file
    Args:
      config: ConfigParser to write out too
      replace: if True, replaces entire credentials file. If False, only over-writes existing sections
    """

    if replace:
        with open(creds_file_path, "w") as creds_file:
            config.write(creds_file)
    else:
        creds = ConfigParser()
        creds.read(filenames=[creds_file_path], encoding="utf-8")
        creds.read_dict(configparser_to_dict(config))
        with open(creds_file_path, "w") as creds_file:
            creds.write(creds_file)

    return


def check_new_profiles() -> dict:

    creds = ConfigParser()
    creds.read(filenames=[creds_file_path], encoding="utf-8")
    existing_profiles = list_profiles_in_db(print_profiles=False)

    new_profiles = dict()
    for section in creds.sections():
        try:
            key_id = creds.get(section, "aws_access_key_id")
            if key_id[:4] == "AKIA" and section not in existing_profiles:
                new_section = {}
                for option in creds.options(section):
                    new_section[option] = creds.get(section, option)
                new_profiles[section] = new_section
        except NoOptionError:
            pass


    # Write new profiles to database
    if len(new_profiles.keys()) > 0:
        new_creds = ConfigParser()
        new_creds.read_dict(new_profiles)
        write_creds_to_db(new_creds)

    return new_profiles


def write_creds_to_db(creds: ConfigParser) -> List[str]:

    conn = sqlite3.connect(sementara_db_path)
    db = conn.cursor()

    for k, section in enumerate(creds.sections()):
        profile = section

        try:
            aws_access_key_id = creds.get(section, "aws_access_key_id")

            # Encrypt secret key
            aws_secret_access_key = encrypt(
                plaintext=creds.get(section, "aws_secret_access_key"),
                app_name=app_name,
                key_name=key_name,
            )
        except NoOptionError:  # doesn't have credentials
            aws_access_key_id = ""
            aws_secret_access_key = ""
            

        other_options = dict()
        for option in creds[section]:
            if option not in ['aws_access_key_id','aws_secret_access_key']:
                other_options[option] = creds.get(section, option)


        db.execute(
            f"INSERT INTO {table_name} (profile, aws_access_key_id, aws_secret_access_key, other_options) VALUES(?,?,?,?)",
            (profile, aws_access_key_id, aws_secret_access_key, json.dumps(other_options)),
        )

    conn.commit()
    conn.close()
    profiles = [profile for profile in creds.sections()]

    return profiles


def remove_profile_from_db(profile_name: str) -> bool:

    conn = sqlite3.connect(sementara_db_path)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()

    try:
        db.execute(f"DELETE FROM {table_name} WHERE profile = ?", (profile_name,))
        conn.commit()
        response = True
    except (IndexError, KeyError):
        print(f"{profile_name} profile not found")
        response = False

    conn.close()
    return response


def check_profile_in_db(profile_name: str) -> bool:

    conn = sqlite3.connect(sementara_db_path)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    db.execute(f"SELECT profile FROM {table_name} WHERE profile=?", (profile_name,))

    try:
        row = [item for item in db]
        response = True
    except (IndexError, KeyError):
        response = False

    return response

def configparser_to_dict(config: ConfigParser) -> dict:

    return {section: dict(config[section]) for section in config.sections()}

