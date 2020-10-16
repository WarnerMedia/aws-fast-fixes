# Lambda Logging

This script will enable Lambda function log groups for all regions in your account.

## Why?

Lambda automatically integrates with CloudWatch Logs and pushes all logs from your code to a CloudWatch Logs group associated with a Lambda function, which is named /aws/lambda/[function name]. If the log group associated with a Lambda function is not found, you'll find the following error in AWS console:

```Log group does not exist
The specific log group: /aws/lambda/<function name> does not exist in this account or region.
```

This script will enable the log groups for corresponding Lambda functions if they don't exist in all regions.

## What the script does.

Thsi script iterates through all the regions returned by ec2:DescribeRegions and if logs:describe_log_groups() with the specified log group name doesn't exist calls logs:create_log_group() to enable with the specified log group name.

## Usage

```bash
usage: enable-lambda-log-group.py [-h] [--debug] [--error] [--timestamp]
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

* [EnableEbsEncryptionByDefault API](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_EnableEbsEncryptionByDefault.html)
* [boto3 list_functions()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.list_functions)
* [boto3 describe_log_groups()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html#CloudWatchLogs.Client.describe_log_groups)
* [boto3 create_log_group()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html#CloudWatchLogs.Client.create_log_group)


