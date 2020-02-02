#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import os
import logging
# logger = logging.getLogger()


def main(args, logger):
    '''Executes the Primary Logic of the Fast Fix'''

    # If they specify a profile use it. Otherwise do the normal thing
    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    # Get all the Regions for this account
    for region in get_regions(session, args):
        ec2_client = session.client("ec2", region_name=region)

        status_response = ec2_client.get_ebs_encryption_by_default()
        if status_response['EbsEncryptionByDefault'] is not True:
            # Make it true
            if args.actually_do_it is True:
                logger.info(f"Enabling Default EBS Encryption in {region}")
                enable_default_encryption(ec2_client, region)
            else:
                logger.info(f"You Need To Enable Default EBS Encryption in {region}")
        else:
            logger.debug(f"Default EBS Encryption is enabled in {region}")



def enable_default_encryption(ec2_client, region):
    '''Actually perform the enabling of default ebs encryption'''
    response = ec2_client.enable_ebs_encryption_by_default()
    if response['EbsEncryptionByDefault'] is True:
        return(True)
    else:
        logger.error(f"Attempt to enable Default EBS Encryption in {region} returned {response}")
        return(False)



def get_regions(session, args):
    '''Return a list of regions with us-east-1 first. If --region was specified, return a list wth just that'''

    # If we specifed a region on the CLI, return a list of just that
    if args.region:
        return([args.region])

    # otherwise return all the regions, us-east-1 first
    ec2 = session.client('ec2')
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="print debugging info", action='store_true')
    parser.add_argument("--error", help="print error info only", action='store_true')
    parser.add_argument("--timestamp", help="Output log with timestamp and toolname", action='store_true')
    parser.add_argument("--region", help="Only Process Specified Region")
    parser.add_argument("--profile", help="Use this CLI profile (instead of default or env credentials)")
    parser.add_argument("--actually-do-it", help="Actually Perform the action", action='store_true')

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