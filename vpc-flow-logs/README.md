# enable-vpc-flowlogs

This script will enable vpc flow logs in your account.

## Why?

VPC Flow Logs is a feature that enables you to capture information about the IP traffic going to and from network interfaces in your VPC. Flowlogs will be delivered to the S3 bucket specified by the value of --flowlog-bucket-prefix with the region appended to the end. It is assumed the S3 Bucket exists and is configured to allow the log service to write to it. After you've created a flow log, you can retrieve and view its data in the chosen destination. 

## What the script does.

This script will iterate through all your regions, through all VPCs in each region and enable flow logs for each VPC.

## Usage

```bash
usage: enable-vpc-flowlogs.py [-h] [--debug] [--error] [--timestamp] [--region REGION] [--profile PROFILE] [--vpc-id VPC_ID] [--actually-do-it] --flowlog-bucket-prefix FLOWLOG_BUCKET_PREFIX

optional arguments:
  -h, --help            show this help message and exit
  --debug               print debugging info
  --error               print error info only
  --timestamp           Output log with timestamp and toolname
  --region REGION       Only Process Specified Region
  --profile PROFILE     Use this CLI profile (instead of default or env credentials)
  --vpc-id VPC_ID       Only Process Specified VPC
  --actually-do-it      Actually Perform the action
  --flowlog-bucket-prefix FLOWLOG_BUCKET_PREFIX S3 bucket to deposit logs to
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.


## AWS Docs

* [VPC Flow Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html)
* [CreateFlowLogs API](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_CreateFlowLogs.html)
* [boto3 create_flow_logs()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.create_flow_logs)


