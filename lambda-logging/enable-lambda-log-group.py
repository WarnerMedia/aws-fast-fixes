#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import os
import logging
import time


def main(args, logger):
    '''Executes the Primary Logic of the Fast Fix'''

    # If they specify a profile use it. Otherwise do the normal thing
    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    # Get all the Regions for this account
    for region in get_regions(session, args):
        lambda_client = session.client("lambda", region_name=region)
        cwlog_client = session.client("logs", region_name=region)

        # Create a reusable Paginator
        paginator = lambda_client.get_paginator('list_functions')

        # Create a PageIterator from the Paginator, parameters here?
        page_iterator = paginator.paginate()

        for page in page_iterator:
            func_list = page['Functions']
            count = 0
            for func in func_list:
                count = count + 1
                if count > 5:
                    # sleep 1 sec after 5 call (limit 5/sec)
                    time.sleep(1)
                    count = 0
                func_name = func.get('FunctionName')
                log_group_name=f"/aws/lambda/{func_name}"
                logs = cwlog_client.describe_log_groups(logGroupNamePrefix=log_group_name)
                if not logs['logGroups']:
                    # log group doesn't exist for this lambda function, creat log group
                    if args.actually_do_it is True:
                        logger.info(f"Creating log group {log_group_name} in {region}")
                        create_log_group(cwlog_client, region, log_group_name)
                    else:
                        logger.info(f"You Need To create log group {log_group_name} in {region}")
                        


def create_log_group(cwlog_client, region, log_group_name):
    '''Actually perform the creation of log group'''
    try:
        cwlog_client.create_log_group(logGroupName=log_group_name)

    except ClientError as e:
        logger.error(f"Attempt to create log group {log_group_name} in {region} returned \"{e}\"")



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

    # create console handler and set level to debug
    logger = logging.getLogger('enable-lambda-log-group')
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