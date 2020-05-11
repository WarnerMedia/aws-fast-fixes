#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import logging
import concurrent.futures

max_workers = 10

def main(args, logger):
    '''Executes the Primary Logic'''

    # If they specify a profile use it. Otherwise do the normal thing
    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    # Get all the Regions for this account
    all_regions = get_regions(session, args)

    # processiong regions
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for region in all_regions:
            futures.append(executor.submit(process_region, args, region, session, logger))
    for future in futures:
        future.result()

    return

def process_region(args, region, session, logger):
    logger.debug(f"Processing region {region}")
    ec2_resource = session.resource('ec2', region_name=region)

    vpcs = []
    for vpc in ec2_resource.vpcs.filter(Filters=[{'Name': 'isDefault', 'Values': ['true']}]):
        if args.vpc_id:
            if args.vpc_id == vpc.id:
                vpcs.append(vpc)
        else:
            vpcs.append(vpc)
    if vpcs:
        for vpc in vpcs:
            if list(vpc.network_interfaces.all()):
                logger.warning("Elastic Network Interfaces exist in the VPC:{}, skipping delete".format(vpc.id))
            else:
                logger.debug("Deleting default VPC:{}, region:{}".format(vpc.id,region))
                if args.actually_do_it:
                    try:
                        vpc_resources = {
                            'internet_gateways': vpc.internet_gateways.all(),
                            'subnets': vpc.subnets.all(),
                            'route_tables': vpc.route_tables.all(),
                            'network_acls': vpc.network_acls.all(),
                            'accepted_vpc_peering_connections': vpc.accepted_vpc_peering_connections.all(),
                            'requested_vpc_peering_connections': vpc.requested_vpc_peering_connections.all(),
                            'security_groups': filter(lambda x:x.group_name != 'default', vpc.security_groups.all()), #exclude default SG
                        }
                        for resource_type in vpc_resources:
                            for resource in vpc_resources[resource_type]:
                                logger.debug("Deleting {}:{}, VPC:{}, region:{}".format(resource_type,resource.id,vpc.id,region))
                                if resource.id.startswith('igw'):
                                    # detach IGW from VPC
                                    resource.detach_from_vpc(VpcId=vpc.id)
                                elif resource.id.startswith('rtb'):
                                    rt_is_main = False
                                    # skip deleting main route tables
                                    for attr in resource.associations_attribute:
                                        if attr['Main']:
                                            rt_is_main = True
                                    if rt_is_main:
                                        continue
                                elif resource.id.startswith('acl'):
                                    if resource.is_default:
                                        # skip deleting default acl
                                        continue

                                resource.delete()
                        vpc.delete()

                    except ClientError as e:
                        if e.response['Error']['Code'] == 'DependencyViolation':
                            logger.error("VPC:{} can't be delete due to dependency, {}".format(vpc.id, e))
                        else:
                            raise
                logger.info("Successfully deleted default VPC:{}, region:{}".format(vpc.id,region))
    else:
        logger.debug("No Default VPC to to be deleted in region:{}".format(region))

    return

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

    if args.exclude_regions:
        exclude_regions = ' '.join(args.exclude_regions).replace(',',' ').split()
        output = list(set(output) - set(exclude_regions))

    return(output)

def do_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="print debugging info", action='store_true')
    parser.add_argument("--error", help="print error info only", action='store_true')
    parser.add_argument("--timestamp", help="Output log with timestamp and toolname", action='store_true')
    parser.add_argument("--profile", help="Use this CLI profile (instead of default or env credentials)")
    parser.add_argument("--region", help="Only look for default VPCs in this region")
    parser.add_argument("--exclude-regions", nargs='+', help="REGION1, REGION2 Do not attempt to delete default VPCs in these regions")
    parser.add_argument("--vpc-id", help="Only delete the VPC specified")
    parser.add_argument("--actually-do-it", help="Actually Perform the action (default behavior is to report on what would be done)", action='store_true')

    args = parser.parse_args()

    return(args)

if __name__ == '__main__':

    args = do_args()

    # Logging idea stolen from: https://docs.python.org/3/howto/logging.html#configuring-logging
    # create console handler and set level to debug
    logger = logging.getLogger('enable-vpc-flowlogs')
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
    # add formatter to ch (console handler)
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    try:
        main(args, logger)
    except KeyboardInterrupt:
        exit(1)