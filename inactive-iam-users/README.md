# Disable Inactive IAM Users

These two scripts will disable inactive IAM Users

`disable-inactive-keys.py` will Disable any API key which has not been used in the last n days (default is 90)

`disable-inactive-login.py` will Disable the LoginProfile (ie Password) of any IAM User who has not logged in in the last n days (default 90)


## Why?

Best Practice is to not leave inactive users who do not have a business justification with access.


## What the disable-inactive-keys script does.

For each user it identifies all active API keys. It then uses get_access_key_last_used() to see the last usage time. If that was more than THRESHOLD days ago, it will disable the Key.

## What the disable-inactive-login script does.

For each user it checks to see if there is a PasswordLastUsed and if a LoginProfile is still attached. If PasswordLastUsed was more than THRESHOLD days ago, it will disable the delete the Login Profile.



## Usage

```bash
usage: disable-inactive-login.py [-h] [--debug] [--error] [--timestamp]
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
                        Number of days of inactivity to disable. Default is 90 days
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.


## AWS Docs

* [GetAccessKeyLastUsed API](https://docs.aws.amazon.com/IAM/latest/APIReference/API_GetAccessKeyLastUsed.html)
* [DeleteLoginProfile API](https://docs.aws.amazon.com/IAM/latest/APIReference/API_DeleteLoginProfile.html)
* [boto3 list_users()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.list_users)
* [boto3 list_access_keys()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.list_access_keys)
* [boto3 get_access_key_last_used()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.get_access_key_last_used)
* [boto3 update_access_key()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.update_access_key)
* [boto3 get_login_profile()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.get_login_profile)
* [boto3 delete_login_profile()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.delete_login_profile)


