# mentaws (moMENTary AWS tokens)

## Introduction

mentaws (pronounced like the candy) is a portmanteau of Moment & AWS.

It's a python package that replaces your aws credentials file with temporary tokens, while keeping your long lived AWS credentials encrypted.

This way, the plaintext credentials file has only temporary tokens. Leaving sensitive long lived tokens encrypted.

## Usage

    $ mentaws setup
    The following 4 were added to mentaws:
    
    👷🏿 Profile
     1.default
     2.mentaws1
     3.mentaws2
     4.mentaws3
    
    $ mentaws refresh
    Generating temporary tokens...

    👷🏿 Profile                    🌎 Region:            ⏰ Tokens expire at
       default                       ap-southeast-1        Tue 19:27 tz:+08
       mentaws1                      ap-southeast-1        Tue 19:27 tz:+08
       mentaws2                      ap-southeast-1        Tue 19:27 tz:+08
       mentaws3                      ap-southeast-1        Tue 19:27 tz:+08
    
    You're ready to go 🚀🚀
    
    $ mentaws remove default
    Are you sure you want to delete default? (y/n): y
    Profile default was deleted
    
## Installation

The simpliest way to install mentaws is to use `pipx`

    $ pipx install mentaws

## Adding profiles

For now, the easiest way to add a profile is to use the generic aws-cli commands:

    $ aws configure --profile produser
    AWS Access Key ID [None]: AKIAI44QH8DHBEXAMPLE
    AWS Secret Access Key [None]: je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY
    Default region name [None]: us-east-1
    Default output format [None]: text

On the next refresh, mentaws will load these new profiles into its database
    
## Implementation details

The AWS credentials are stored in a sqlite3 database in the same directory as your AWS directory.

When you first setup mentaws, a randomly generated key is generated and stored in your macOS keychain. This key is then used to encrypt the `aws_secret_access_key`. All other fields like the profile names and `aws_access_key_id` are stored in plaintext.

For the encryption we use the [pyca/cryptography](https://cryptography.io/en/latest/fernet.html#implementation) package, which implements the following:
* AES in CBC mode with a 128-bit key for encryption; using PKCS7 padding.
* HMAC using SHA256 for authentication.
* Initialization vectors are generated using os.urandom().

We store the randomly generated key in your macOS keychain using keyring, this has one limitation, namely:

* Any Python script or application can access secrets created by keyring from that same Python executable without the operating system prompting the user for a password. **To cause any specific secret to prompt for a password every time it is accessed, locate the credential using the Keychain Access application, and in the Access Control settings, remove Python from the list of allowed applications.**

## Warning

This project is still in beta, and work with all AWS features, use at your own risk.
    
 