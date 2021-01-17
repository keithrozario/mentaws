import boto3

iam_client = boto3.client('iam')

response = iam_client.list_virtual_mfa_devices()
for mfa_device in response['VirtualMFADevices']:
    r_deactivate = iam_client.deactivate_mfa_device(
        UserName='mentawsAdminUser',
        SerialNumber=mfa_device['SerialNumber']
    )
    r = iam_client.delete_virtual_mfa_device(
        SerialNumber=mfa_device['SerialNumber']
    )
    print(r)

print(response)

