#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import os
import logging
import json
# logger = logging.getLogger()


def main(args, logger):
    '''Executes the Primary Logic of the Fast Fix'''

    # If they specify a profile use it. Otherwise do the normal thing
    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    # If necessary, get the org info once
    if args.create_org_cmk:
        org_client = session.client("organizations", region_name="us-east-1")
        org_info = org_client.describe_organization()['Organization']
        sts_client = session.client("sts", region_name="us-east-1")
        account_id = sts_client.get_caller_identity()['Account']


    # Get all the Regions for this account
    for region in get_regions(session, args):
        ec2_client = session.client("ec2", region_name=region)
        kms_client = session.client("kms", region_name=region)

        # First we must Determine what the key is, and if it needs to change
        key_response = ec2_client.get_ebs_default_kms_key_id()
        key_id = key_response['KmsKeyId']
        logger.debug(f"Current Default key is {key_id} in {region}")
        # At this point, key_id will either be the full ARN, or "alias/aws/ebs"
        # So you can pass in a number of things (alias, alias_arn, key_id, but this call always has the key arn)

        if args.KeyId:
            # Need to get the actual key _arn_
            new_key_details = get_kms_key_if_exists(kms_client, key_id)
            if new_key_details is False:
                logger.critical(f"Unable to find key {args.KeyId} in {region}. Aborting")
                exit(1)
            new_key_arn = new_key_details['KeyMetadata']['Arn']
            logger.info(f"Found {args.KeyId} with key arn of {new_key_arn}")


        elif args.create_cmk is True:
            key_alias = 'alias/default-ebs-cmk'

            # First see if we need to create a new key
            existing_key = get_kms_key_if_exists(kms_client, key_alias)
            if existing_key:
                logger.warning(f"KMS Key with alias {key_alias} already exists")
                new_key_arn = existing_key['KeyMetadata']['Arn']
            elif args.actually_do_it:
                logger.info(f"Creating new KMS Key with alias {key_alias}")
                new_key_arn = create_cmk(kms_client, region, key_alias)
            else:
                logger.info(f"Would create a custom CMK with alias {key_alias}")
                new_key_arn = None

        elif args.create_org_cmk is True:
            key_alias = 'alias/default-org-ebs-cmk'

            # First see if we need to create a new key
            existing_key = get_kms_key_if_exists(kms_client, key_alias)
            if existing_key:
                logger.warning(f"KMS Key with alias {key_alias} already exists")
                new_key_arn = existing_key['KeyMetadata']['Arn']
            elif args.actually_do_it:
                logger.info(f"Creating new org-wide KMS Key with alias {key_alias}")
                new_key_arn = create_org_cmk(kms_client, org_info, account_id, region, key_alias)
            else:
                logger.info(f"Would create a custom org-wide CMK with alias {key_alias}")
                new_key_arn = None

        else:
            # If none of the above were specificed, then no change is needed below
            new_key_arn = key_id

        # See if the default key needs to be changed
        if new_key_arn != key_id:
            # we need to change they key
            if args.actually_do_it:
                logger.info(f"Setting Default Key to {new_key_arn}. Was {key_id}")
                ec2_client.modify_ebs_default_kms_key_id(KmsKeyId=new_key_arn)
            elif new_key_arn is None:
                logger.info(f"Would attempt to set the default EBS Key to the new key. Was {key_id}")
            else:
                try:
                    ec2_client.modify_ebs_default_kms_key_id(KmsKeyId=new_key_arn, DryRun=True)
                except ClientError as e:
                    if e.response['Error']['Code'] == "DryRunOperation":
                        logger.info(f"Would attempt to set Default Key to {new_key_arn}. Was {key_id}")
                    else:
                        logger.error(f"DryRun setting Default Key to {new_key_arn} from {key_id} Failed. Error: {e}")
        else:
            # It doesn't
            logger.info(f"Default EBS Encryption is currently set to {key_id}")


        # Then ensure the EBS Encryption is set correctly
        status_response = ec2_client.get_ebs_encryption_by_default()
        if status_response['EbsEncryptionByDefault'] is not True and not args.disable:
            # Make it true
            if args.actually_do_it is True:
                logger.info(f"Enabling Default EBS Encryption in {region}")
                enable_default_encryption(ec2_client, region)

            else:
                logger.info(f"You Need To Enable Default EBS Encryption in {region}")
        elif status_response['EbsEncryptionByDefault'] is True and args.disable:
            # Make it false
            if args.actually_do_it is True:
                logger.info(f"Disabling Default EBS Encryption in {region}")
                disable_default_encryption(ec2_client, region)

            else:
                logger.info(f"Would Disable Default EBS Encryption in {region}")
        else:
            logger.debug(f"Default EBS Encryption is enabled in {region}")


def get_kms_key_if_exists(kms_client, key_id):
    try:
        key_details = kms_client.describe_key(KeyId=key_id)
        return(key_details)
    except ClientError as e:
        if e.response['Error']['Code'] == "NotFoundException":
            return(False)
        else:
            raise


def create_org_cmk(client, org_info, account_id, region, key_alias):
    '''Create a new CMK for use with EBS'''
    org_id = org_info['Id']
    logger.debug(f"Creating key for {org_id}")

    policy = {
        "Version": "2012-10-17",
        "Id": "EBS Key Policy For Organization",
        "Statement": [
            {
                "Sid": "Enable IAM User Permissions",
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{account_id}:root"
                },
                "Action": "kms:*",
                "Resource": "*"
            },
            {
                "Sid": "Allow EBS use of the KMS key for organization",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "*"
                },
                "Action": [
                    "kms:Decrypt",
                    "kms:DescribeKey",
                    "kms:Encrypt",
                    "kms:ReEncrypt*",
                    "kms:GetKeyPolicy"
                ],
                "Resource": "*",
                "Condition": {
                    "StringEquals": {
                        "kms:ViaService": f"ec2.{region}.amazonaws.com",
                        "aws:PrincipalOrgID": org_id
                    }
                }
            }
        ]
    }

    logger.debug(f"Creating key with Policy:\n{json.dumps(policy, indent=2)}")

    response = client.create_key(
        Policy=json.dumps(policy),
        Description=f"Default EBS Key for {region} Shared across org {org_id}",
        Origin='AWS_KMS',
        BypassPolicyLockoutSafetyCheck=False
    )
    key = response['KeyMetadata']
    client.create_alias(
        AliasName=key_alias,
        TargetKeyId=key['KeyId']
    )
    print(f"Created Key {key['KeyId']} in {region} with ARN of {key['Arn']}")
    return(key['Arn'])


def create_cmk(client, region, key_alias):
    '''Create a new CMK for use with EBS'''
    response = client.create_key(
        # Policy='string',
        Description=f"Default EBS Key for {region}",
        Origin='AWS_KMS',
        BypassPolicyLockoutSafetyCheck=False
    )
    key = response['KeyMetadata']
    client.create_alias(
        AliasName=key_alias,
        TargetKeyId=key['KeyId']
    )
    print(f"Created Key {key['KeyId']} in {region} with ARN of {key['Arn']}")
    return(key['Arn'])


def enable_default_encryption(ec2_client, region):
    '''Actually perform the enabling of default ebs encryption'''
    response = ec2_client.enable_ebs_encryption_by_default()
    if response['EbsEncryptionByDefault'] is True:
        return(True)
    else:
        logger.error(f"Attempt to enable Default EBS Encryption in {region} returned {response}")
        return(False)


def disable_default_encryption(ec2_client, region):
    '''Actually perform the enabling of default ebs encryption'''
    response = ec2_client.disable_ebs_encryption_by_default()
    if response['EbsEncryptionByDefault'] is False:
        return(True)
    else:
        logger.error(f"Attempt to disable Default EBS Encryption in {region} returned {response}")
        return(False)


def get_regions(session, args):
    '''Return a list of regions with us-east-1 first. If --region was specified, return a list wth just that'''

    # If we specifed a region on the CLI, return a list of just that
    if args.region:
        return([args.region])

    # otherwise return all the regions, us-east-1 first
    ec2 = session.client('ec2', region_name="us-east-1")
    response = ec2.describe_regions()
    output = ['us-east-1']
    for r in response['Regions']:
        # return us-east-1 first, but dont return it twice
        if r['RegionName'] == "us-east-1":
            continue
        output.append(r['RegionName'])
    return(output)


def do_args():
    import argparse

    key_id_message = """You can specify KEYID using any of the following:
    Key ID. For example, 1234abcd-12ab-34cd-56ef-1234567890ab.
    Key alias. For example, alias/ExampleAlias.
    Key ARN. For example, arn:aws:kms:us-east-1:012345678910:key/1234abcd-12ab-34cd-56ef-1234567890ab.
    Alias ARN. For example, arn:aws:kms:us-east-1:012345678910:alias/ExampleAlias.

Note: Amazon Web Services authenticates the KMS key asynchronously. Therefore, if you specify an ID, alias, or ARN that is not valid, the action can appear to complete, but eventually fails."""

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=key_id_message)

    parser.add_argument("--debug", help="print debugging info", action='store_true')
    parser.add_argument("--error", help="print error info only", action='store_true')
    parser.add_argument("--timestamp", help="Output log with timestamp and toolname", action='store_true')
    parser.add_argument("--region", help="Only Process Specified Region")
    parser.add_argument("--profile", help="Use this CLI profile (instead of default or env credentials)")
    parser.add_argument("--actually-do-it", help="Actually Perform the action", action='store_true')
    parser.add_argument("--disable", help="Disable Default Encryption rather than enable it.", action='store_true')

    cmk_group = parser.add_mutually_exclusive_group()
    cmk_group.add_argument("--create-cmk", help="Create an AWS CMK in each region for use with EBS Default Encryption", action='store_true')
    cmk_group.add_argument("--create-org-cmk", help="Create an AWS CMK with org-wide permissions in each region ", action='store_true')
    cmk_group.add_argument("--use-cmk-id", dest="KeyId", help="Enable Default Encryption with this existing key_id.")

    args = parser.parse_args()

    return(args)

if __name__ == '__main__':

    args = do_args()

    # Logging idea stolen from: https://docs.python.org/3/howto/logging.html#configuring-logging
    # create console handler and set level to debug
    logger = logging.getLogger('enable-ebs-default-encryption')
    ch = logging.StreamHandler()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.error:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)

    # Silence Boto3 & Friends
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    # create formatter
    if args.timestamp:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        formatter = logging.Formatter('%(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    try:
        main(args, logger)
    except KeyboardInterrupt:
        exit(1)