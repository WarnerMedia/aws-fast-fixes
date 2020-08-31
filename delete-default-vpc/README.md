# Default VPC Deletion

This script will attempt to delete default VPCs in the account. It will abort if it detects any ENI's exist (meaning there are resources in the VPC)

## Why?

AWS best practices call for a two or three tier network architecture with internet facing, compute and data being seperated into different security zone. Additionally unused VPCs in regions that aren't being used provide places for attackers to create resources.


## What the script does.

This script will iterate through all the regions in your account return by `aws ec2 describe-regions` and look for default VPCs. If it finds a default VPC, it will look to see if any Elastic Network Interfaces (ENIs) exist. The presense of an ENI in a VPC indicate that some resource exists in the VPC (RDS, EC2, Redshift, Lambda, NatGateways, etc). If an ENI is present it will output a warning and proceed no further.

If no ENIs exist, it will delete all the resources in the VPC including the subnets, NACLS, default secruity group and the VPC itself. <TODO: validate this list of resources deleted>


## Usage

```bash
usage: delete-default-vpcs.py [-h] [--debug] [--error] [--timestamp]
                                        [--profile PROFILE]
                                        [--region REGION]
                                        [--exclude-regions REGION1, REGION2] 
                                        [--vpc-id] VPCID
                                        [--boto-region] REGION
                                        [--actually-do-it]


optional arguments:
  -h, --help            show this help message and exit
  --debug               print debugging info
  --error               print error info only
  --timestamp           Output log with timestamp and toolname
  --profile PROFILE     Use this CLI profile (instead of default or env credentials)
  --region REGION       Only look for default VPCs in this region
  --boto-region REGION  Initial AWS region for boto3 client (defaults to us-east-1)
  --exclude-regions REGION1, REGION2  Do not attempt to delete default VPCs in these regions
  --vpc-id VPCID        Only delete the VPC specified (must match --region )
  --actually-do-it      Actually Perform the action (default behavior is to report on what would be done)

```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.



## AWS Docs

TODO: Document the API BOTO3 calls necessary
* [Amazon S3 Block Public Access](https://aws.amazon.com/s3/features/block-public-access/) Feature Docs
* [PutPublicAccessBlock](https://docs.aws.amazon.com/goto/WebAPI/s3-2006-03-01/PutPublicAccessBlock) API
* [boto3 list_buckets()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_buckets)
* [boto3 get_public_access_block()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.get_public_access_block)
* [boto3 put_public_access_block()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_public_access_block)
* [boto3 get_bucket_acl()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.get_bucket_acl)
* [boto3 get_bucket_policy()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.get_bucket_policy)


