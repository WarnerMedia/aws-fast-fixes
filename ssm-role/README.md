# SSM Role

This script will create a ssm role for ec2 instance.  Instances without an instance profile (role) will be attached to the newly created ssm role.  Instances with an existing role will have ssm permissions added to that role.

## Why?

SSM manager requires the agent to be installed as well as basic iam permissions.


## What the script does.

Insures all running ec2 instances have `arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore` attached.

**Warning!!!** Prevent configuration drift by running with this script with `--also-attach-to-existing-roles` only after updating Cloudformation, Terraform, Pulumi, etc.

## Usage

```bash
usage: ssm-role.py    [--profile PROFILE] [--region REGION] [--actually-do-it] [--also-attach-to-existing-roles] [--role ROLE] [--policy POLICY]

optional arguments:
  -h, --help                      Show this help message and exit
  --region                        Only Process Specified Region
  --profile PROFILE               Use this CLI profile (instead of default or env credentials)
  --actually-do-it                Actually Perform the action
  --also-attach-to-existing-roles Adds permissions to existing roles
  --role                          Name of role
  --policy                        Policy ARN to attach to role if instance already has IAM profile attached to ec2
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.
