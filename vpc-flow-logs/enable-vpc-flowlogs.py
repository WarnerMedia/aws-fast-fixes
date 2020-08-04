#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import logging

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
    for region in all_regions:
        process_region(args, region, session, logger)

    return

def process_region(args, region, session, logger):
    logger.info(f"Processing region {region}")
    ec2_client = session.client('ec2', region_name=region)
    vpcs = []
    paginator = ec2_client.get_paginator('describe_vpcs')
    for page in paginator.paginate():
        for vpc in page['Vpcs']:
            if args.vpc_id:
                if args.vpc_id == vpc['VpcId']:
                    vpcs.append(vpc['VpcId'])
            else:
                vpcs.append(vpc['VpcId'])
    if vpcs:
        # processing VPCs
        for VpcId in vpcs:
            # enable flowlogs if the vpc has eni within it
            logger.debug(f"   Processing VpcId {VpcId}")
            network_interfaces = ec2_client.describe_network_interfaces(Filters=[{'Name':'vpc-id','Values':[VpcId]}])['NetworkInterfaces']
            if network_interfaces:
                logger.debug(f"   ENI found in VpcId {VpcId}")
                enable_flowlogs(VpcId, ec2_client, args, region)
            else:
                logger.debug(f"   No ENI found in VpcId {VpcId}, skipped.")
    else:
        logger.debug("   No VPCs to enable flow logs in region:{}".format(region))

    return


def enable_flowlogs(VpcId,client,args,region):
    # checking for existing flow logs
    bucket = 'arn:aws:s3:::{}'.format(args.flowlog_bucket)
    paginator = client.get_paginator('describe_flow_logs')
    for page in paginator.paginate(
            Filters=[
                {
                    'Name': 'resource-id',
                    'Values': [VpcId]
                },
                {
                    'Name': 'log-destination-type',
                    'Values': ['s3']
                }
            ]
        ):
        
        if page['FlowLogs']:

            for FlowLog in page['FlowLogs']:
                if FlowLog['LogDestination'] == bucket:
                    
                    accept_destructive_update=False

                    logger.debug("   Flow Log ({}) already exist, region:{}, VPC:{}".format(FlowLog['FlowLogId'],region,VpcId))
                    if FlowLog['DeliverLogsStatus'] == 'FAILED':
                        logger.error("Flow Log ({}) failed, region:{}, VPC:{}, please check it".format(FlowLog['FlowLogId'],region,VpcId))
                        return

                    logger.debug("Flow Log ({}) is {} on {}\n   traffic type: {}\n   destination type: {}\n   destination: {}\n   log format: \n   {}".format(
                        FlowLog['FlowLogId'],
                        FlowLog['FlowLogStatus'],
                        FlowLog['ResourceId'],
                        FlowLog['TrafficType'],
                        FlowLog['LogDestinationType'],
                        FlowLog['LogDestination'],
                        FlowLog['LogFormat']
                    ))

                    difflist = []
                    if FlowLog['TrafficType'] != args.traffic_type:
                        difflist.append("Traffic type will change from {} to {}.".format(FlowLog['TrafficType'],args.traffic_type))
                    if FlowLog['LogDestination'] != bucket:
                        difflist.append("Log Destination will change from {} to {}.".format(FlowLog['LogDestination'],bucket))

                    if difflist == []:
                        # No actions to perform here
                        continue

                    logger.info("Existing flow log will be terminated and new flow log created with these changes:\n\t{}\n".format(difflist))

                    if args.force:
                        accept_destructive_update='y'
                    else:
                        accept_destructive_update = input(f'Do you wish to continue? [y/N] ').lower()
                    if accept_destructive_update[:1] == 'y':
                        delete_flowlog(VpcId,FlowLog['FlowLogId'],True,client,args,region)
                        create_flowlog(VpcId,bucket,client,args,region)
                    else:
                        logger.info("User declined replacement of flow log {}".format(FlowLog['FlowLogId']))
                else:
                    create_flowlog(VpcId,bucket,client,args,region)
        else:
            create_flowlog(VpcId,bucket,client,args,region)

    return

def delete_flowlog(VpcId, FlowLogId, actually_do_it, client, args, region):
    if args.actually_do_it:
        logger.debug("   deleting Flow Log:{}, region:{}, VPC:{}".format(FlowLogId,region,VpcId))
        response = client.delete_flow_logs(
             DryRun=not actually_do_it,
             FlowLogIds=[FlowLogId]
        )
        if response.get('Unsuccessful'):
            for failure in response['Unsuccessful']:
                if failure.get('Error'):
                    logger.error("Flow Log deletion failed, error:{}".format(failure['Error'].get('Message')))
        else:
            logger.info("Successfully deleted Flow Log:{}, region:{}, VPC:{}".format(FlowLogId,region,VpcId))
    else:
        logger.info("Would delete Flow Log:{}, region:{}, VPC:{}".format(FlowLogId,region,VpcId))
    return

def create_flowlog(VpcId,bucket,client,args,region):
    # creating flow logs
    if args.actually_do_it:
        logger.debug("enabling Flow Log region:{}, VPC:{}".format(region,VpcId))
        response = client.create_flow_logs(
            ResourceIds=[VpcId],
            ResourceType='VPC',
            TrafficType=args.traffic_type,
            LogDestinationType='s3',
            LogDestination=bucket
        )

        if response.get('Unsuccessful'):
            for unsuccess in response['Unsuccessful']:
                if unsuccess.get('Error'):
                    logger.error("Flow Log creation failed, error:{}".format(unsuccess['Error'].get('Message')))
        elif response.get('FlowLogIds'):
            logger.info("Successfully created Flow Logs:{}, region:{}, VPC:{}".format(response['FlowLogIds'][0],region,VpcId))
    else:
        logger.info("Would Enable Flow Log region:{}, VPC:{}".format(region,VpcId))
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
    return(output)


def do_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="print debugging info", action='store_true')
    parser.add_argument("--error", help="print error info only", action='store_true')
    parser.add_argument("--timestamp", help="Output log with timestamp and toolname", action='store_true')
    parser.add_argument("--region", help="Only Process Specified Region")
    parser.add_argument("--profile", help="Use this CLI profile (instead of default or env credentials)")
    parser.add_argument("--vpc-id", help="Only Process Specified VPC")
    parser.add_argument("--actually-do-it", help="Actually Perform the action", action='store_true')
    parser.add_argument("--flowlog-bucket", help="S3 bucket to deposit logs to", required=True)
    parser.add_argument("--traffic-type", help="The type of traffic to log", default='ALL', choices=['ACCEPT','REJECT','ALL'])
    parser.add_argument("--force", help="Perform flowlog replacement without prompt", action='store_true')

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
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    try:
        main(args, logger)
    except KeyboardInterrupt:
        exit(1)