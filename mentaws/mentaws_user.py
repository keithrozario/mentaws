import boto3
import pyotp
import time
from datetime import datetime

cf_client = boto3.client('cloudformation')

with open('cf_template.yml','r') as cf_template:
    template_body = cf_template.read()

response = cf_client.create_stack(
    StackName='mentawsUser',
    TemplateBody=template_body,
    TimeoutInMinutes=3,
    Capabilities=[
        'CAPABILITY_NAMED_IAM',
    ],
)
stack_id = response['StackId']

while True:
    time.sleep(5)
    status = cf_client.describe_stacks(
        StackName='mentawsUser',
    )['Stacks'][0]['StackStatus']
    if 'FAILED' in status or 'COMPLETE' in status:
        break
    else:
        print(status)

# User created, create MFA Device
iam_client = boto3.client('iam')

response = iam_client.create_virtual_mfa_device(
    VirtualMFADeviceName='mentawsMFA'
)

serial_number = response['VirtualMFADevice']['SerialNumber']
seed = response['VirtualMFADevice']['Base32StringSeed']

# # Setup TOTP
totp = pyotp.TOTP(seed)
now = datetime.now()
current_code = totp.at(for_time=now, counter_offset=0)
next_code = totp.at(for_time=now, counter_offset=1)

# Associate with user
response = iam_client.enable_mfa_device(
    UserName='mentawsAdminUser',
    SerialNumber=serial_number,
    AuthenticationCode1=current_code,
    AuthenticationCode2=next_code,
)

# Delete
response = iam_client.deactivate_mfa_device(
    UserName='mentawsAdminUser',
    SerialNumber=serial_number,
)
response = iam_client.delete_virtual_mfa_device(
    SerialNumber=serial_number
)

response = cf_client.delete_stack(
    StackName='mentawsUser',
)
