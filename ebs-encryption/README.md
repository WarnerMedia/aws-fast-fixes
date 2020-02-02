# EBS Encryption

This script will enable automatic EBS encryption for all regions in your account.

## Why?

Encryption-at-rest is a key security best practice. However when creating instances, remembering to check the box or retrofitting existing automations can be risky or time consuming. In May of 2019, AWS released a feature to enable all newly created EBS volumes to use an AWS or Customer Managed KMS Key.  This script will enable that feature in all regions.

## What the script does.

Thsi script iterates through all the regions returned by ec2:DescribeRegions and if get_ebs_encryption_by_default() is false calls enable_ebs_encryption_by_default() to enable with a Default AWS Managed Key.

**Warning!!!** Per AWS: *After you enable encryption by default, you can no longer launch instances using instance types that do not support encryption. For more information, see [Supported Instance Types](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html#EBSEncryption_supported_instances).*

## Usage

```bash
usage: enable-ebs-default-encryption.py [-h] [--debug] [--error] [--timestamp]
                                        [--region REGION] [--profile PROFILE]
                                        [--actually-do-it]

optional arguments:
  -h, --help         show this help message and exit
  --debug            print debugging info
  --error            print error info only
  --timestamp        Output log with timestamp and toolname
  --region REGION    Only Process Specified Region
  --profile PROFILE  Use this CLI profile (instead of default or env credentials)
  --actually-do-it   Actually Perform the action
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.


## AWS Docs

* [Feature Announcement](https://aws.amazon.com/blogs/aws/new-opt-in-to-default-encryption-for-new-ebs-volumes/)
* [EnableEbsEncryptionByDefault API](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_EnableEbsEncryptionByDefault.html)
* [boto3 get_ebs_encryption_by_default()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.get_ebs_encryption_by_default)
* [boto3 enable_ebs_encryption_by_default()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.enable_ebs_encryption_by_default)


