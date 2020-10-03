import boto3
import os
from configparser import ConfigParser
from .operations import get_platform_config


def get_token(key_id: str, secret_access_key: str, duration_seconds: int, region: str = 'ap-southeast-1') -> dict:
    """
    :param key_id: AWS key id
    :param secret_access_key: AWS secret access key
    :param region: AWS region
    :param duration_seconds: Duration of access keys
    :return: Dict containing temporary key_id, secret_access_key, and session_token
    """
    client = boto3.client(
        'sts',
        region_name=region,
        endpoint_url=f'https://sts.{region}.amazonaws.com',
        aws_access_key_id=key_id,
        aws_secret_access_key=secret_access_key,)

    response = client.get_session_token(
        DurationSeconds=duration_seconds
    )

    token = {
        "aws_access_key_id": response['Credentials']['AccessKeyId'],
        "aws_secret_access_key": response['Credentials']['SecretAccessKey'],
        "aws_session_token": response['Credentials']['SessionToken'],
    }

    return token


def get_aws_config() -> ConfigParser:
    """
    :param config_file_path: path to aws config file
    :return:
    """
    platform_config = get_platform_config()
    config_file_path = os.path.join(platform_config['aws_directory'], platform_config['config_file_name'])

    aws_config = ConfigParser()
    aws_config.read(config_file_path)

    return aws_config


def get_region(aws_config: ConfigParser, section: str, config: dict) -> str:

    try:
        region = aws_config[section]['region']
    except KeyError:
        region = config['default_region']

    return region