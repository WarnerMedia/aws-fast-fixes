#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import os
import logging
import json


def main(args, logger):
    '''Executes the Primary Logic of the Fast Fix'''

    # If they specify a profile use it. Otherwise do the normal thing
    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    # Get all the Regions for this account. CloudFront is only in us-east-1
    if args.resource_type == "CloudFront":
        all_regions = ["us-east-1"]
    else:
        all_regions = get_regions(session, args)

    count = 0
    subscription = get_subscription(session)
    if subscription is None:
        logger.critical(f"Shield Advanced is not enabled in account {args.profile}. Aborting")
        exit(1)

    # Get the list of protected resource. These we do not have to process again
    protections = get_protected_resources(session)

    for region in all_regions:
        logger.debug(f"Processing {region}")
        shield_client = session.client("shield", region_name=region)

        if args.resource_type == "ALB":
            unprotected_arns = get_all_albs(protections, session, region)
        elif args.resource_type == "APIGW":
            unprotected_arns = get_all_apigw(protections, session, region)
        elif args.resource_type == "CloudFront":
            unprotected_arns = get_all_cloudfront(protections, session, region)
        else:
            print(f"Invalid resource type: {args.resource_type}")
            exit(1)

        for arn, name in unprotected_arns.items():
            count += 1
            if args.actually_do_it:
                enable_protection(shield_client, arn, name)
            else:
                logger.info(f"Would enable Shield Protection on {name} ({arn})")

    logger.info(f"{args.profile} has {count} {args.resource_type} resources without Shield Advanced Protection")


def get_subscription(session):
    client = session.client("shield")
    try:
        subscription = client.describe_subscription()['Subscription']
        # logger.debug(json.dumps(subscription, indent=2, sort_keys=True, default=str))
    except ClientError as e:
        if e.response['Error']['Code'] == "ResourceNotFoundException":
            subscription = None
        else:
            logger.critical(f"Unable to describe the subscription: {e}")
            exit(1)
    except Exception as e:
        logger.critical(f"Unable to describe the subscription: {e}")
        exit(1)
    return(subscription)


def get_protected_resources(session):
    # It doesn't matter which region I make this call from
    shield_client = session.client("shield")
    protections = []
    response = shield_client.list_protections()
    while 'NextToken' in response:
        protections += response['Protections']
        response = shield_client.list_protections(NextToken=response['NextToken'])
    protections += response['Protections']

    arns = []
    for p in protections:
        arns.append(p['ResourceArn'])
    return(arns)


def enable_protection(shield_client, arn, name):
    '''Actually perform the enabling of Key rotation and checking of the status code'''
    logger.info(f"Enabling Shield Protection on {arn}")
    try:
        response = shield_client.create_protection(Name=name, ResourceArn=arn)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return(True)
        else:
            logger.error(f"Attempt to enable shield protection for {arn} returned {response}")
            return(False)
    except ClientError as e:
        raise


def get_all_cloudfront(protections, session, region):
    output = {}
    client = session.client('cloudfront', region_name=region)
    response = client.list_distributions(MaxItems="1000")
    if 'Items' not in response['DistributionList']:
        # Empty CF List.
        return(output)
    for cf in response['DistributionList']['Items']:
        # if lb['Type'] != 'application':
        #     # Don't care
        #     continue
        # if lb['Scheme'] != 'internet-facing':
        #     # Also Don't care
        #     continue
        if cf['ARN'] in protections:
            logger.debug(f"Arn {cf['ARN']} is already protected by Shield Advanced")
            continue
        output[cf['ARN']] = f"{cf['DomainName']} ({cf['Id']})"
    return(output)


def get_all_albs(protections, session, region):
    output = {}
    client = session.client('elbv2', region_name=region)
    response = client.describe_load_balancers()
    for lb in response['LoadBalancers']:
        if lb['Type'] != 'application':
            # Don't care
            continue
        if lb['Scheme'] != 'internet-facing':
            # Also Don't care
            continue
        if lb['LoadBalancerArn'] in protections:
            logger.debug(f"Arn {lb['LoadBalancerArn']} is already protected by Shield Advanced")
            continue
        output[lb['LoadBalancerArn']] = lb['LoadBalancerName']
    return(output)


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
    parser.add_argument("--resource-type", help="Type of resource to apply Shield Protections to", required=True, choices=['ALB', 'CloudFront'])

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