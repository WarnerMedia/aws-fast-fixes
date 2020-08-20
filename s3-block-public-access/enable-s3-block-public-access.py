#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import os
import json
import logging
# logger = logging.getLogger()


def main(args, logger):
    '''Executes the Primary Logic of the Fast Fix'''

    # If they specify a profile use it. Otherwise do the normal thing
    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    # Open the command file for writing if we're supposed to do so
    if args.filename:
        f = open(args.filename, "w")
    else:
        f = None

    # S3 is a global service and we can use any regional endpoint for this.
    s3_client = session.client("s3")
    for bucket in get_all_buckets(s3_client):
        try:
            status_response = s3_client.get_public_access_block(Bucket=bucket)
            if 'PublicAccessBlockConfiguration' not in status_response:
                logger.error(f"Unable to get PublicAccessBlockConfiguration for bucket: {bucket}. This is not expected and nothing will be done.")
                continue
            if (status_response['PublicAccessBlockConfiguration']['BlockPublicAcls'] is True and
                status_response['PublicAccessBlockConfiguration']['IgnorePublicAcls'] is True and
                status_response['PublicAccessBlockConfiguration']['BlockPublicPolicy'] is True and
                status_response['PublicAccessBlockConfiguration']['RestrictPublicBuckets'] is True):
                logger.debug(f"Bucket {bucket} already has all four block public access settings enabled")
                continue
            else:
                fix_bucket(s3_client, bucket, args, f)
                continue
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                fix_bucket(s3_client, bucket, args, f)
            elif e.response['Error']['Code'] == 'AccessDeniedException':
                logger.warning(f"Unable to get details of key {bucket}: AccessDenied")
                continue
            else:
                raise


    if args.filename:
        f.close()

def fix_bucket(s3_client, bucket, args, f=None):
    '''Determine if the Bucket is safe to fix. Do the fix or write the AWS CLI or just notify based on args '''
    if not is_safe_to_fix_bucket(s3_client, bucket):
        logger.warning(f"Bucket {bucket} has a bucket policy, conflicting ACLs or Website Hosting enabled which could conflict with Block Public Access. Not Enabling it.")
        return(False)
    elif args.actually_do_it is True:
        logger.info(f"Enabling Block Public Access on {bucket}")
        rc = enable_block_public_access(s3_client, bucket)
        return(rc)
    elif f is not None:
        logger.info(f"You Need To Enable Block Public Access on {bucket}. Writing AWS CLI command")
        command = f"\necho 'Enabling Block Public Access on {bucket}'\n"
        command += f"aws s3api put-public-access-block --bucket {bucket} "
        command += "--public-access-block-configuration BlockPublicAcls=True,IgnorePublicAcls=True,BlockPublicPolicy=True,RestrictPublicBuckets=True"
        if args.profile:
            command += f"--profile {args.profile}"
        command += "\n"
        f.write(command)
    else:
        logger.info(f"You Need To Enable Block Public Access on {bucket}")
        return(True)

def is_safe_to_fix_bucket(s3_client, bucket_name):
    '''Check ACLS and Policy to see if Bucket is safe to fix'''
    return(is_safe_to_fix_by_acl(s3_client, bucket_name) and is_safe_to_fix_by_policy(s3_client, bucket_name) and is_safe_to_fix_by_bucket_website(s3_client, bucket_name))


def is_safe_to_fix_by_acl(s3_client, bucket_name):
    '''Inspect Bucket ACLS and determine if this bucket is safe to fix'''

    try:
        response = s3_client.get_bucket_acl(Bucket=bucket_name)
        for grant in response['Grants']:
            if grant['Grantee']['Type'] == "Group":
                if grant['Grantee']['URI'] == "http://acs.amazonaws.com/groups/global/AuthenticatedUsers":
                    return(False)
                elif grant['Grantee']['URI'] == "http://acs.amazonaws.com/groups/global/AllUsers":
                    return(False)
        return(True)  # Safe if we hit this point
    except ClientError as e:
        logger.error(f"ClientError getting Bucket {bucket_name} ACL: {e} ")
        return(False)  # Not Safe if we get this error

def is_safe_to_fix_by_policy(s3_client, bucket_name):
    '''Inspect the Bucket Policy to make sure there are no conditions granting access that could conflict with this'''

    try:
        response = s3_client.get_bucket_policy(Bucket=bucket_name)
        if 'Policy' in response:
            policy = json.loads(response['Policy'])
            for s in policy['Statement']:
                if s['Effect'] == "Deny":
                    continue  # We don't need to worry about these
                if 'Principal' in s:
                    if 'AWS' in s['Principal']:
                        if s['Principal']['AWS'] == "*":
                            return(False)  # Bucket is public, review is needed
                    if s['Principal'] == "*":
                        return(False)  # Bucket is public, review is needed
        # No match, we must be good!
        return(True)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
            # No Bucket Policy is safe
            return(True)
        else:
            raise

def is_safe_to_fix_by_bucket_website(s3_client, bucket_name):
    '''Inspect Bucket Website and determine if this bucket is safe to fix'''

    try:
        s3_client.get_bucket_website(Bucket=bucket_name)
        logger.warning(f"Bucket {bucket_name} is Hosting a Website!")
        return(False)  # Not Safe, Bucket Website Hosting enabled
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchWebsiteConfiguration':
            # No Bucket Website Hosting
            return(True)
        else:
            raise

def enable_block_public_access(s3_client, bucket_name):
    '''Actually perform the enabling of block public access and checking of the status code'''
    response = s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
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
    parser.add_argument("--output-script", dest="filename", help="Write CLI Commands to FILENAME for later execution")

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
