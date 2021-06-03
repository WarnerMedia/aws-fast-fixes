# enable-shield-protection

This script will enable Shield Advanced Protections on all the resources of the specified type

## Why?

AWS Shield Advanced is an enterprise-grade anti-DDOS service. Leveraging AWS's control of the underlying network, and the ability to manage AWS WAF, they can provide a superior anti-DDOS capability than a normal company.

## What the script does.

**NOTE:** This script will not run if the AWS Shield Advanced Subscription is not enabled.

This script will iterate though all AWS Regions and make the CreateProtection call for any unprotected resources of the specified type (Currently: CloudFront and ALB).


## Usage

```bash
usage: enable-shield-protection.py [-h] [--debug] [--error] [--timestamp]
                                  [--region REGION] [--actually-do-it] [--resource-type]

optional arguments:
  -h, --help        show this help message and exit
  --debug           print debugging info
  --error           print error info only
  --timestamp       Output log with timestamp and toolname
  --region REGION   Only Process Specified Region
  --profile PROFILE  Use this CLI profile (instead of default or env credentials)
  --actually-do-it  Actually Perform the action
  --resource-type {ALB,CloudFront} Type of resource to apply Shield Protections to
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.


## AWS Docs

* [Adding AWS Shield Advanced protection to AWS resources](https://docs.aws.amazon.com/waf/latest/developerguide/configure-new-protection.html)
* [CreateProtection API](https://docs.aws.amazon.com/waf/latest/DDOSAPIReference/API_CreateProtection.html)
* [boto3 create_protection()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/shield.html#Shield.Client.create_protection)

Other ReadOnly calls made:
* [boto3 describe_load_balancers()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.describe_load_balancers)
* [boto3 list_distributions()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudfront.html#CloudFront.Client.list_distributions)
* [boto3 list_protections()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/shield.html#Shield.Client.list_protections)
* [boto3 describe_subscription()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/shield.html#Shield.Client.describe_subscription)