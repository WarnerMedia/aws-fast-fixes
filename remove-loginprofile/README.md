# Remove Login Profile with No MFA

This script will disable the ability for an IAM User to login to the AWS Console for all IAM Users that have a console password (LoginProfile) and do _not_ have MFA enabled. The script can optionally exclude users that have used their account in N number of days


## Why?

Enabling Multi-factor-authentication is a common requirement for all privileged accounts. In most all cases IAM Users have privileged access to cloud APIs for the purposes of starting and stopping machines, accessing sensitive data in S3, etc.

## What the ./remove-loginprofile-no-mfa.py script does.

This script will first list all IAM Users. It will then look to see if the IAM User has a console password (called a LoginProfile). If the user has a LoginProfile, it checks to make sure the User also has MFA Enabled.

If MFA is not enabled, and --threshold is not set, it will remove the user's console password.

If --threshold is set, it will check to see if the PasswordLastUsed exists and was not within *threshold* days. If both of those are true it will remove the user's console password.

If the user never logged in (PasswordLastUsed does not exist), it will ensure the user was not _created_ in the last *threshold* days, and then remove the user's console password.

This script will *NOT* remove the user's console password unless --actually-do-it is specified. This script will not delete the user, nor will it delete or deactivate the user's Access Keys. **The removal of the user's console password is irreversible.** Once removed, it cannot be reapplied because the password is not known to the AWS account. AWS does not provide an option to disable the user's password.




## Usage

```bash
usage: remove-loginprofile-no-mfa.py [-h] [--debug] [--error] [--timestamp]
                                     [--profile PROFILE] [--actually-do-it]
                                     [--threshold THRESHOLD]

optional arguments:
  -h, --help            show this help message and exit
  --debug               print debugging info
  --error               print error info only
  --timestamp           Output log with timestamp and toolname
  --profile PROFILE     Use this CLI profile (instead of default or env credentials)
  --actually-do-it      Actually Perform the action
  --threshold THRESHOLD
                        Only Disable Login Profile if inactive for this many days
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.


## AWS Docs

* [DeleteLoginProfile API](https://docs.aws.amazon.com/IAM/latest/APIReference/API_DeleteLoginProfile.html)
* [boto3 list_users()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.list_users)
* [boto3 list_mfa_devices()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.list_mfa_devices)
* [boto3 delete_login_profile()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.delete_login_profile)
* [boto3 get_login_profile()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.get_login_profile)
