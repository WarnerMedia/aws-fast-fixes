# Organizations Delegated Access

These scripts will configure Delegated Administrator in a payer account for GuardDuty and IAM Access Analyzer.

## Why?

*With AWS Organizations you can perform account management activities at scale by consolidating multiple AWS accounts into a single organization. Consolidating accounts simplifies how you use other AWS services. You can leverage the multiaccount management services available in AWS Organizations with select AWS services to perform tasks on all accounts that are members of your organization.[link](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_integrated-services-list.html)*

The concept of Delegated Admin accounts for specific services is new. It allows the Organization master to grant an account in the organization full ability to deploy and manage the service in all accounts in the Organization. This eliminates the need for teams to login the payer account or individually deploy tooling in an organization's child accounts.


## What the delegate-admin script does.

This script will enable delegated admin for IAM Access Analyzer (plus any future services).

Then, because GuardDuty has to be special, the script iterates through all the regions returned by ec2:DescribeRegions. It will then call enable_organization_admin_account() to configure GuardDuty's delegated admin.

The script will report if the organization has delegated to another child account, or if the delegation was already configured before attempting to enable account delegation.

## Usage

```bash
usage: delegate-admin.py [-h] [--debug] [--error] [--timestamp]
                           [--region REGION] [--profile PROFILE]
                           [--actually-do-it] [--delegated-admin ADMIN_ACCOUNT_ID]

optional arguments:
  -h, --help            show this help message and exit
  --debug               print debugging info
  --error               print error info only
  --timestamp           Output log with timestamp and toolname
  --region REGION       Only Process Specified Region
  --profile PROFILE     Use this CLI profile (instead of default or env credentials)
  --actually-do-it      Actually Perform the action
  --delegated-admin ADMIN_ACCOUNT_ID
                        Account that the payer will delegate access to
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.

## What the delegate-guardduty script does.

This script iterates through all the regions returned by ec2:DescribeRegions. It will then call enable_organization_admin_account() to configure GuardDuty's delegated admin.

The script will report if the organization has delegated to another child account, or if the delegation was already configured before attempting to enable account delegation.

## Usage

```bash
usage: delegate-guardduty.py [-h] [--debug] [--error] [--timestamp]
                           [--region REGION] [--profile PROFILE]
                           [--actually-do-it] [--delegated-admin ADMIN_ACCOUNT_ID]

optional arguments:
  -h, --help            show this help message and exit
  --debug               print debugging info
  --error               print error info only
  --timestamp           Output log with timestamp and toolname
  --region REGION       Only Process Specified Region
  --profile PROFILE     Use this CLI profile (instead of default or env credentials)
  --actually-do-it      Actually Perform the action
  --delegated-admin ADMIN_ACCOUNT_ID
                        Account that the payer will delegate access to
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.



## AWS Docs

* [AWS services that you can use with AWS Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_integrated-services-list.html) - reference the "Supports Delegated Administrator column"

* [Product Page](https://aws.amazon.com/organizations/)
* Organizations [RegisterDelegatedAdministrator API](https://docs.aws.amazon.com/organizations/latest/APIReference/API_RegisterDelegatedAdministrator.html)
* GuardDuty [EnableOrganizationAdminAccount](https://docs.aws.amazon.com/goto/WebAPI/guardduty-2017-11-28/EnableOrganizationAdminAccount)
* [boto3 organizations.register_delegated_administrator()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/organizations.html#Organizations.Client.register_delegated_administrator)
* [boto3 guardduty.enable_organization_admin_account()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/guardduty.html#GuardDuty.Client.enable_organization_admin_account)