import os
from mentaws import config

if __name__ == '__main__':

    platform_config = config.get_platform_config()
    creds_path = os.path.join(platform_config["aws_directory"], platform_config["creds_file_name"])

    if len(os.environ.get('CREDENTIALS_FILE_CONTENTS', "")) > 0:
        with open(creds_path,'w') as cred_file:
            cred_file.write(os.environ.get('CREDENTIALS_FILE_CONTENTS', ""))
        print("env:CREDENTIALS found, loading")
    else:
        print("env:CREDENTIALS_FILE_CONTENTS not found, using file instead")

