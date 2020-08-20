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
    all_regions = get_regions(session, args)

    for region in all_regions:
        logger.debug(f"Processing {region}")
        kms_client = session.client("kms", region_name=region)
        keys = get_all_keys(kms_client)
        for k in keys:
            try:
                status_response = kms_client.get_key_rotation_status(KeyId=k)
                if 'KeyRotationEnabled' not in status_response:
                    logger.error(f"Unable to get KeyRotationEnabled for keyid: {k}")
                    continue
                if status_response['KeyRotationEnabled']:
                    logger.debug(f"KeyId {k} already has rotation enabled")
                else:
                    if args.actually_do_it is True:
                        logger.info(f"Enabling KMS Key Rotation on KeyId {k}")
                        enable_key_rotation(kms_client, k)
                    else:
                        logger.info(f"You Need To Enable KMS Key Rotation on KeyId {k}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'AccessDeniedException':
                    logger.warning(f"Unable to get details of key {k} in {region}: AccessDenied")
                    continue
                else:
                    raise

def enable_key_rotation(kms_client, KeyId):
    '''Actually perform the enabling of Key rotation and checking of the status code'''
    try:
        response = kms_client.enable_key_rotation(KeyId=KeyId)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return(True)
        else:
            logger.error(f"Attempt to enable key rotation for {KeyId} returned {response}")
            return(False)
    except ClientError as e:
        if e.response['Error']['Code'] == 'KMSInvalidStateException':
            logger.warning(f"KMS Key {KeyId} is pending deletion")
            return(True)
        else:
            raise

def get_all_keys(kms_client):
    '''Return an array of all KMS keys for this region'''
    keys = []
    response = kms_client.list_keys()
    while response['Truncated']:
        keys += response['Keys']
        response = kms_client.list_keys(Marker=response['NextMarker'])
    keys += response['Keys']

    key_ids = []
    for k in keys:
        key_ids.append(k['KeyId'])
    return(key_ids)


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
    logger = logging.getLogger('kms-key-rotation')
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