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

    # S3 is a global service and we can use any regional endpoint for this.
    s3_client = session.client("s3")
    for bucket in get_all_buckets(s3_client):
        try:
            status_response = s3_client.get_bucket_encryption(Bucket=bucket)
            if 'ServerSideEncryptionConfiguration' not in status_response and 'Rules' not in status_response['ServerSideEncryptionConfiguration']:
                logger.error(f"Unable to get ServerSideEncryptionConfiguration for bucket: {bucket}")
                continue
            if len(status_response['ServerSideEncryptionConfiguration']['Rules']) == 1:
                enc_type = status_response['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
                logger.debug(f"Bucket {bucket} already has encryption enabled: {enc_type}")
            else:
                logger.warning(f"Bucket {bucket} has more than 1 rule. This is not expected and nothing will be done")
                continue
        except ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                if not is_safe_to_fix_bucket(s3_client, bucket):
                    logger.warning(f"Bucket {bucket} has a bucket policy that could conflict with Default Encryption. Not Enabling it.")
                    continue
                elif args.actually_do_it is True:
                    logger.info(f"Enabling Default Encryption on {bucket}")
                    enable_bucket_encryption(s3_client, bucket)
                else:
                    logger.info(f"You Need To Enable Default Encryption on {bucket}")
            elif e.response['Error']['Code'] == 'AccessDeniedException':
                logger.warning(f"Unable to get details of key {bucket}: AccessDenied")
                continue
            else:
                raise

def is_safe_to_fix_bucket(s3_client, bucket_name):
    '''Inspect the Bucket Policy to make sure there are no conditions requiring encryption that could conflict with this'''

    match_strings = [ 'x-amz-server-side-encryption', 'x-amz-server-side-encryption-aws-kms-key-id']

    try:
        response = s3_client.get_bucket_policy(Bucket=bucket_name)
        if 'Policy' in response:
            policy_str = response['Policy']
            for condition in match_strings:
                if condition in policy_str:
                    return(False)
        # No match, we must be good!
        return(True)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
            # No Bucket Policy is safe
            return(True)
        else:
            raise


def enable_bucket_encryption(s3_client, bucket_name):
    '''Actually perform the enabling of default encryption and checking of the status code'''
    # raise NotImplementedError
    response = s3_client.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'} }]
        }
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return(True)
    else:
        logger.error(f"Attempt to enable default encryption for {bucket_name} returned {response}")
        return(False)


def get_all_buckets(s3_client):
    '''Return an array of all S3 bucket names'''
    buckets = []
    response = s3_client.list_buckets()  # Don't paginate
    for b in response['Buckets']:
        buckets.append(b['Name'])
    return(buckets)


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
    parser.add_argument("--profile", help="Use this CLI profile (instead of default or env credentials)")
    parser.add_argument("--actually-do-it", help="Actually Perform the action", action='store_true')

    args = parser.parse_args()

    return(args)

if __name__ == '__main__':

    args = do_args()

    # Logging idea stolen from: https://docs.python.org/3/howto/logging.html#configuring-logging
    # create console handler and set level to debug
    logger = logging.getLogger('s3-default-encryption')
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