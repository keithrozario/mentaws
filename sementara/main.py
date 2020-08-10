import getpass
import configparser
from aws_operations import get_aws_config, get_token, get_region
from operations import load_conf_file, setup_conf_file, encrypt_creds_file, decrypt_creds_file, write_creds_file

if __name__ == '__main__':
    p = "passwordsafafa"
    p2 = "passwordsafafa"

    try:
        config = load_conf_file()
    except FileNotFoundError:
        config = setup_conf_file()
        p = getpass.getpass(prompt='Enter encryption password: ')
        p2 = getpass.getpass(prompt='Confirm Password: ')
        if p == p2:
            encrypt_creds_file(password=p, salt=config['salt'])
            print("AWS credentials encrypted, run sementara again to generate new creds")
            exit(1)
        else:
            print("Passwords do no match, aborting...")
            exit(1)

    # Decrypt credentials file
    p = getpass.getpass(prompt='Enter decryption password: ')
    data = decrypt_creds_file(password=p, salt=config['salt'])
    print("Credentials file decrypted...")
    creds = configparser.ConfigParser()cat
    creds.read_string(data)

    # get AWS configuration
    aws_config = get_aws_config()
    temp_config = configparser.ConfigParser()

    # Generate temp credentials
    print("Generating temporary tokens...")
    for section in creds.sections():
        region = get_region(aws_config=aws_config, config=config, section=section)
        temp_token = get_token(
            key_id=creds[section]['aws_access_key_id'],
            secret_access_key=creds[section]['aws_secret_access_key'],
            duration_seconds=config['default_duration_seconds'],
            region=region,
        )
        temp_config[section] = temp_token
        print(f"Obtained tokens for profile: {section}")

    # Replace ~/.aws/credentials
    print("Writing out temporary credentials file...")
    write_creds_file(temp_config)
    print("Credentials file ready, you're ready to go...")