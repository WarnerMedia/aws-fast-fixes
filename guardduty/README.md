# GuardDuty

This script will create a GuardDuty Detector in all regions in your account. If --accept-invite is specified it will accept any open invitations from the specified account id.

## Why?

*[GuardDuty](https://aws.amazon.com/guardduty/) is a threat detection service that continuously monitors for malicious activity and unauthorized behavior to protect your AWS accounts and workloads.  With GuardDuty, you now have an intelligent and cost-effective option for continuous threat detection in the AWS Cloud. The service uses machine learning, anomaly detection, and integrated threat intelligence to identify and prioritize potential threats. GuardDuty analyzes tens of billions of events across multiple AWS data sources, such as AWS CloudTrail, Amazon VPC Flow Logs, and DNS logs.*

## What the script does.

This script iterates through all the regions returned by ec2:DescribeRegions. If a GuardDuty Detector is not present it will create one with a FindingPublishingFrequency set to 'ONE_HOUR'.

If --accept-invite ACCOUNT_ID is specified, it will accept the invitation if present. Otherwise it will output a warning.


**Note:** GuardDuty will incur costs in your account. My experience is that is approximately 1% - 2% of the overall account spend. See the [Pricing Page](https://aws.amazon.com/guardduty/pricing/) for more specifics.


## Usage

```bash
usage: enable-guardduty.py [-h] [--debug] [--error] [--timestamp]
                           [--region REGION] [--profile PROFILE]
                           [--actually-do-it] [--accept-invite MASTERID]

optional arguments:
  -h, --help            show this help message and exit
  --debug               print debugging info
  --error               print error info only
  --timestamp           Output log with timestamp and toolname
  --region REGION       Only Process Specified Region
  --profile PROFILE     Use this CLI profile (instead of default or env credentials)
  --actually-do-it      Actually Perform the action
  --accept-invite MASTERID
                        Accept an invitation (if present) from this AccountId
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.


## AWS Docs

* [Product Page](https://aws.amazon.com/guardduty/)
* [CreateDetector API](https://docs.aws.amazon.com/goto/WebAPI/guardduty-2017-11-28/CreateDetector)
* [AcceptInvitation API](https://docs.aws.amazon.com/goto/WebAPI/guardduty-2017-11-28/AcceptInvitation)
* [boto3 list_detectors()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/guardduty.html#GuardDuty.Client.list_detectors)
* [boto3 list_invitations()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/guardduty.html#GuardDuty.Client.list_invitations)
* [boto3 create_detector()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/guardduty.html#GuardDuty.Client.create_detector)
* [boto3 accept_invitation()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/guardduty.html#GuardDuty.Client.accept_invitation)

