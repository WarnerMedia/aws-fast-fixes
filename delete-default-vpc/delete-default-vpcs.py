#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import logging
import os

max_workers = 10

def main(args, logger):
    '''Executes the Primary Logic'''

    session = boto3.Session(profile_name=args.profile, region_name=args.boto_region)

    # Get all the Regions for this account
    all_regions = get_regions(session, args)

    # processiong regions
    for region in all_regions:
        process_region(args, region, session, logger)

    return

def delete_igw(vpc,logger):
    for igw in vpc.internet_gateways.all():
        logger.debug("Detaching {}, VPC:{}".format(igw.id,vpc.id))
        igw.detach_from_vpc(VpcId=vpc.id)
        logger.debug("Deleting {}, VPC:{}".format(igw.id,vpc.id))
        igw.delete()

def delete_eigw(vpc,logger):
    client = vpc.meta.client
    paginator = client.get_paginator('describe_egress_only_internet_gateways')
    for page in paginator.paginate():
        for eigw in page['EgressOnlyInternetGateways']:
            for attachment in eigw['Attachments']:
                if attachment['VpcId'] == vpc.id and attachment['State'] == 'attached':
                    logger.debug("Deleting {}, VPC:{}".format(eigw['EgressOnlyInternetGatewayId'],vpc.id))
                    client.delete_egress_only_internet_gateway(EgressOnlyInternetGatewayId=eigw['EgressOnlyInternetGatewayId'])
                    break

def delete_subnet(vpc,logger):
    for subnet in vpc.subnets.all():
        logger.debug("Deleting {}, VPC:{}".format(subnet.id,vpc.id))
        subnet.delete()

def delete_sg(vpc,logger):
    for sg in filter(lambda x:x.group_name != 'default', vpc.security_groups.all()): #exclude default SG:
        logger.debug("Deleting {}, VPC:{}".format(sg.id,vpc.id))
        sg.delete()

def delete_rtb(vpc,logger):
    for rtb in vpc.route_tables.all():
        rt_is_main = False
        # skip deleting main route tables
        for attr in rtb.associations_attribute:
            if attr['Main']:
                rt_is_main = True
        if rt_is_main:
            continue
        logger.debug("Deleting {}, VPC:{}".format(rtb.id,vpc.id))
        rtb.delete()

def delete_acl(vpc,logger):
    for acl in vpc.network_acls.all():
        if acl.is_default:
            # skip deleting default acl
            continue
        logger.debug("Deleting {}, VPC:{}".format(acl.id,vpc.id))
        acl.delete()

def delete_pcx(vpc,logger):
    pcxs = list(vpc.accepted_vpc_peering_connections.all()) + list(vpc.requested_vpc_peering_connections.all())
    for pcx in pcxs:
        if pcx.status['Code'] == 'deleted':
            # vpc peering connections already deleted
            continue
        logger.debug("Deleting {}, VPC:{}".format(pcx.status,vpc.id))
        pcx.delete()

def delete_endpoints(vpc,logger):
    client = vpc.meta.client
    paginator = client.get_paginator('describe_vpc_endpoints')
    for page in paginator.paginate(Filters=[
                    {'Name': 'vpc-id', 'Values': [vpc.id]},
                    {'Name': 'vpc-endpoint-state', 'Values': ['pendingAcceptance', 'pending', 'available', 'rejected', 'failed']},
                ]):
        for endpoint in page['VpcEndpoints']:
            logger.debug("Deleting {}, VPC:{}".format(endpoint['VpcEndpointId'],vpc.id))
            client.delete_vpc_endpoints(VpcEndpointIds=[endpoint['VpcEndpointId']])

def delete_cvpn_endpoint(vpc,logger):
    client = vpc.meta.client
    paginator = client.get_paginator('describe_client_vpn_endpoints')
    for page in paginator.paginate():
        for cvpn_endpoint in page['ClientVpnEndpoints']:
            if cvpn_endpoint['VpcId'] == vpc.id:
                logger.debug("Deleting {}, VPC:{}".format(cvpn_endpoint['ClientVpnEndpointId'],vpc.id))
                client.delete_client_vpn_endpoint(ClientVpnEndpointId=[cvpn_endpoint['ClientVpnEndpointId']])

def delete_vgw(vpc,logger):
    client = vpc.meta.client
    response = client.describe_vpn_gateways(Filters=[
                    {'Name': 'attachment.vpc-id', 'Values': [vpc.id]},
                    {'Name': 'state', 'Values': ['pending', 'available']},
                ])
    for vgw in response['VpnGateways']:
        for attachment in vgw['VpcAttachments']:
            if attachment['State'] in ['attaching','attached']:
                logger.debug("Detaching {}, from VPC:{}".format(vgw['VpnGatewayId'],vpc.id))
                client.detach_vpn_gateway(VpcId=vpc.id, VpnGatewayId=vgw['VpnGatewayId'])
                break
        response = client.describe_vpn_connections(Filters=[{'Name': 'vpn-gateway-id', 'Values': [vgw['VpnGatewayId']]}])
        for vpn_connection in response['VpnConnections']:
            if vpn_connection['State'] in ['pending','available']:
                logger.debug("Deleting {}, from VPC:{}".format(vpn_connection['VpnConnectionId'],vpc.id))
                client.delete_vpn_connection(VpnConnectionId=vpn_connection['VpnConnectionId'])
        logger.debug("Deleting {}, VPC:{}".format(vgw['VpnGatewayId'],vpc.id))
        client.delete_vpn_gateway(VpnGatewayId=vgw['VpnGatewayId'])

def delete_vpc(vpc,logger,region,debug):
    network_interfaces = list(vpc.network_interfaces.all())
    if network_interfaces:
        logger.warning("Elastic Network Interfaces exist in the VPC:{}, skipping delete".format(vpc.id))
        if debug:
            for eni in network_interfaces:
                logger.debug("Interface:{} attached to {},  VPC:{}, region:{}".format(eni.id,eni.attachment,vpc.id,region))
        return
    else:
        logger.info("Deleting default VPC:{}, region:{}".format(vpc.id,region))
        if args.actually_do_it:
            try:
                vpc_resources = {
                    # dependency order from https://aws.amazon.com/premiumsupport/knowledge-center/troubleshoot-dependency-error-delete-vpc/
                    'internet_gateways': delete_igw,
                    'egress_only_internet_gateways': delete_eigw,
                    'subnets': delete_subnet,
                    'route_tables': delete_rtb,
                    'network_acls': delete_acl,
                    'vpc_peering_connections': delete_pcx,
                    'vpc_endpoints': delete_endpoints,
                    # nat gateways (we do not delete this for safety)
                    'security_groups': delete_sg,
                    # instances (we do not delete this for safety)
                    # 'client_vpn_endpoints': delete_cvpn_endpoint, skip deleting because it use network interfaces
                    'virtual_private_gateways': delete_vgw,
                    # network interfaces (we do not delete this for safety)
                }
                for resource_type in vpc_resources:
                    vpc_resources[resource_type](vpc,logger)

                vpc.delete()

            except ClientError as e:
                if e.response['Error']['Code'] == 'DependencyViolation':
                    logger.error("VPC:{} can't be delete due to dependency, {}".format(vpc.id, e))
                else:
                    raise

            logger.info("Successfully deleted default VPC:{}, region:{}".format(vpc.id,region))
        if not args.actually_do_it:
            logger.info("Would delete default VPC:{}, region:{}".format(vpc.id,region))

def process_region(args, region, session, logger):
    logger.info(f"Processing region {region}")
    ec2_resource = session.resource('ec2', region_name=region)

    vpcs = []
    for vpc in ec2_resource.vpcs.filter(Filters=[{'Name': 'isDefault', 'Values': ['true']}]):
        logger.debug(f'Found {vpc}')
        if args.vpc_id:
            if args.vpc_id == vpc.id:
                vpcs.append(vpc)
        else:
            vpcs.append(vpc)
    if vpcs:
        for vpc in vpcs:
            delete_vpc(vpc,logger,region,args.debug)
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
    parser.add_argument("--boto-region", help="Initial AWS region for boto3 client", default=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
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