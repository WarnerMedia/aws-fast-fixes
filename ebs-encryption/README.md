# EBS Encryption

This script will enable automatic EBS encryption for all regions in your account.

## Why?

Encryption-at-rest is a key security best practice. However when creating instances, remembering to check the box or retrofitting existing automations can be risky or time consuming. In May of 2019, AWS released a feature to enable all newly created EBS volumes to use an AWS or Customer Managed KMS Key.  This script will enable that feature in all regions.

## What the script does.

This script iterates through all the regions returned by ec2:DescribeRegions and if get_ebs_encryption_by_default() is false calls enable_ebs_encryption_by_default() to enable with a Default AWS Managed Key.

**Warning!!!** Per AWS: *After you enable encryption by default, you can no longer launch instances using instance types that do not support encryption. For more information, see [Supported Instance Types](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html#EBSEncryption_supported_instances).*

**Second Warning!!!** Enabling EBS encryption using the service managed key will prevent you from sharing AMIs outside of the account. If you need to share AMIs in your organization, you will want to specify the `--create-org-cmk` flag. This will create a new KMS CMK that is shared to your Org. See below for the key policy it will create:

## Usage

```bash
usage: enable-ebs-default-encryption.py [-h] [--debug] [--error] [--timestamp] [--region REGION]
                                        [--profile PROFILE] [--actually-do-it] [--disable]
                                        [--create-cmk | --create-org-cmk | --use-cmk-id KEYID]

optional arguments:
  -h, --help         show this help message and exit
  --debug            print debugging info
  --error            print error info only
  --timestamp        Output log with timestamp and toolname
  --region REGION    Only Process Specified Region
  --profile PROFILE  Use this CLI profile (instead of default or env credentials)
  --actually-do-it   Actually Perform the action
  --disable           Disable Default Encryption rather than enable it.
  --create-cmk        Create an AWS CMK in each region for use with EBS Default Encryption
  --create-org-cmk    Create an AWS CMK with org-wide permissions in each region
  --use-cmk-id KEYID  Enable Default Encryption with this existing key_id.

You can specify KEYID using any of the following:
    Key ID. For example, 1234abcd-12ab-34cd-56ef-1234567890ab.
    Key alias. For example, alias/ExampleAlias.
    Key ARN. For example, arn:aws:kms:us-east-1:012345678910:key/1234abcd-12ab-34cd-56ef-1234567890ab.
    Alias ARN. For example, arn:aws:kms:us-east-1:012345678910:alias/ExampleAlias.

Note: Amazon Web Services authenticates the KMS key asynchronously. Therefore, if you specify an ID, alias, or ARN that is not valid, the action can appear to complete, but eventually fails.

```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.

### Org Wide Key Policy
```json
{
    "Version": "2012-10-17",
    "Id": "EBS Key Policy For Organization",
    "Statement": [
        {
            "Sid": "Enable IAM User Permissions",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789012:root"
            },
            "Action": "kms:*",
            "Resource": "*"
        },
        {
            "Sid": "Allow EBS use of the KMS key for organization",
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Action": [
                "kms:Decrypt",
                "kms:DescribeKey",
                "kms:Encrypt",
                "kms:ReEncrypt*",
                "kms:GetKeyPolicy"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:PrincipalOrgID": "o-xxxxxxx",
                    "kms:ViaService": "ec2.us-east-1.amazonaws.com"
                }
            }
        }
    ]
}
```


## AWS Docs

* [Feature Announcement](https://aws.amazon.com/blogs/aws/new-opt-in-to-default-encryption-for-new-ebs-volumes/)
* [EnableEbsEncryptionByDefault API](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_EnableEbsEncryptionByDefault.html)
* [boto3 get_ebs_encryption_by_default()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.get_ebs_encryption_by_default)
* [boto3 enable_ebs_encryption_by_default()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.enable_ebs_encryption_by_default)


