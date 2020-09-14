#!/bin/env python3
import boto3
from botocore.exceptions import ClientError
from collections import OrderedDict
import argparse
import logging
import json

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

def format_tags(item: dict, tags='Tags'):
    '''Returns dict of tags or empty dict'''
    tags_list = item.get(tags)
    return OrderedDict(sorted([(tag.get('Key'), tag.get('Value')) for tag in tags_list])) if tags_list is not None else OrderedDict()

def get_ec2(session, regions, state='running'):
    '''Generator for all running ec2 instances'''
    for region in regions:
        ec2 = session.client('ec2', region_name=region)
        reservations = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': [state]}])['Reservations']
        for reservation in reservations:
            for instance in reservation['Instances']:
                instance['Region'] = region
                instance['Tags'] = format_tags(instance)
                instance['Name'] = instance['Tags'].get('Name', '')
                yield instance

def get_account(session):
    '''Returns AWS account'''
    return session.client('sts').get_caller_identity().get('Account')

def get_role_name(session, profile_name):
    ''' Returns the instance profile'''
    return session.client('iam').get_instance_profile(InstanceProfileName=profile_name)['InstanceProfile']['Roles'][0]['RoleName']

def get_role_policy(session, role_name):
    '''Returns list of policies attached to role'''
    policies = session.client('iam').list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
    return [p.get('PolicyArn') for p in policies]

def attach_instance_profile(session, instance_id, region, profile_name):
    '''Attaches instance profile to e2 instance'''
    account = get_account(session)
    session.client('ec2', region_name=region).associate_iam_instance_profile(
        IamInstanceProfile={
            "Arn" :  f"arn:aws:iam::{account}:instance-profile/{profile_name}",
            "Name": profile_name
        },
        InstanceId=instance_id
    )

def attach_policy_to_role(session, role_name, policy_arn):
    '''Attaches policy to role'''
    session.client('iam').attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)

def attach_role(session, instance_id, instance_name, region, role_name, args):
    '''Attaches IAM instance profile (role) to ec2 instance'''
    if args.actually_do_it:
        logging.info(f"InstanceId: {instance_id}, Name: {instance_name} attaching IAM Role: {role_name}")
        attach_instance_profile(session, instance_id, region, role_name)
    else:
        logging.warning(f"InstanceId: {instance_id}, Name: {instance_name} has no IAM Role attached.  Will attach IAM Role: {role_name}")

def audit_role(session, instance_id, instance_name, instance_profile, policy_arn, actually_do_it):
    '''Audit role already attached to instance to ensure policy is present'''
    role_name = get_role_name(session, instance_profile)
    policies = get_role_policy(session, role_name)

    if policy_arn not in policies:
        if args.actually_do_it and args.also_attach_to_existing_roles:
            logging.info(f"Role: {role_name}, Instance Profile {instance_profile}, attaching {policy_arn}")
            attach_policy_to_role(session, role_name, policy_arn)
        else:
            logging.warning(f"Role: {role_name}, Instance Profile {instance_profile}, InstanceId: {instance_id}, Name: {instance_name} does not have {policy_arn} attached")

def do_args():
    '''Returns command line args'''
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", help="Only Process Specified Region")
    parser.add_argument("--profile", help="Use this CLI profile (instead of default or env credentials)")
    parser.add_argument("--role", help="Name of role", default='ssm_common')
    parser.add_argument("--policy", help="Policy arn to attach to role if instance already has IAM profile attached to ec2", default='arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore')
    parser.add_argument("--actually-do-it", help="Actually Perform the action", action='store_true')
    parser.add_argument("--also-attach-to-existing-roles", help="Adds permissions to existing roles", action='store_true')
    args = parser.parse_args()
    return(args)

def create_ssm_role(session, role_name, policy_arn, args):
    try:
        get_role_name(session, role_name)
    except:
        if args.actually_do_it:
            logging.info(f"Creating Role: {role_name}, Instance Profile: {role_name}, Policy {policy_arn}")

            iam = session.client('iam')
            trust_policy={
                "Version": "2012-10-17",
                "Statement": [
                    {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                    }
                ]
            }
            iam.create_role(
                Path='/',
                RoleName=role_name,
                Description="SSM agent role for ec2",
                PermissionsBoundary=policy_arn,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': role_name
                    },
                    {
                        'Key': 'Description',
                        'Value': 'Created by aws-fast-fix ssm-role.py'
                    },
                ]
            )
            iam.create_instance_profile (
                InstanceProfileName =role_name 
            )

            iam.add_role_to_instance_profile (
                InstanceProfileName = role_name,
                RoleName            = role_name 
            )
            attach_policy_to_role(session, role_name, policy_arn)
        else:
            logging.warning(f"Role: {role_name}, Instance Profile: {role_name}, Policy {policy_arn} will be created")

if __name__ == '__main__':
    # logging
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    # aws
    args = do_args()
    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    try:
        create_ssm_role(session, args.role, args.policy, args)
        regions = get_regions(session, args)
        for instance in get_ec2(session, regions, state="running"):
            instance_id = instance.get('InstanceId')
            instance_name = instance.get('Name')
            region = instance.get('Region')
            if 'IamInstanceProfile' not in instance:
                attach_role(session, instance_id, instance_name, region, args.role, args)
            else:
                instance_profile = instance['IamInstanceProfile']['Arn'].split('instance-profile/')[-1]
                audit_role(session, instance_id, instance_name, instance_profile, args.policy, args)
    except KeyboardInterrupt:
        exit(1)
