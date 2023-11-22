# EBS Block Public Access

This script will enable Block Public Access for EBS in all regions in your account.

## Why?

While there are a few valid use-cases for sharing a hard drive to every AWS customer, those probably don't apply to you. But it is easy to accidentally share an EBS Snapshot and threat actors scan for those regularly. AWS recently accounts [Block Public Access](https://aws.amazon.com/about-aws/whats-new/2023/11/amazon-elastic-block-store-public-access-ebs-snapshots/) for EBS.  This script will enable that feature in all regions.

## What the script does.

This script iterates through all the regions returned by ec2:DescribeRegions and if get_snapshot_block_public_access_state() is `unblocked` calls enable_snapshot_block_public_access() to enable blocking _all_ sharing.

## Usage

```bash
usage: ebs-block-public-access.py [-h] [--debug] [--error] [--timestamp]
                                  [--region REGION] [--profile PROFILE]
                                  [--actually-do-it] [--disable]

options:
  -h, --help         show this help message and exit
  --debug            print debugging info
  --error            print error info only
  --timestamp        Output log with timestamp and toolname
  --region REGION    Only Process Specified Region
  --profile PROFILE  Use this CLI profile (instead of default or env credentials)
  --actually-do-it   Actually Perform the action
  --disable          Disable Block Public Access rather than enable it.

```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.


## AWS Docs

* [Feature Announcement](https://aws.amazon.com/about-aws/whats-new/2023/11/amazon-elastic-block-store-public-access-ebs-snapshots/)
* [EnableSnapshotBlockPublicAccess API](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_EnableSnapshotBlockPublicAccess.html)
* [boto3 get_snapshot_block_public_access_state()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/get_snapshot_block_public_access_state.html)
* [boto3 enable_snapshot_block_public_access()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/enable_snapshot_block_public_access.html)


