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
        guardduty_client = session.client("guardduty", region_name=region)

        status_response = guardduty_client.list_detectors()
        if len(status_response['DetectorIds']) == 0:
            # Make it true
            if args.actually_do_it is True:
                logger.info(f"Enabling GuardDuty in {region}")
                detector_id = enable_guarduty(guardduty_client, region)
            else:
                logger.info(f"You Need To Enable GuardDuty in {region}")
                continue
        else:
            detector_id = status_response['DetectorIds'][0]
            logger.debug(f"GuardDuty is enabled in {region}")

        if args.MasterId is None:
            continue  # Not doing invite acceptance

        # Now do the invitations
        invite_response = guardduty_client.list_invitations() # probably need to support paganation
        for i in invite_response['Invitations']:
            if i['AccountId'] != args.MasterId:
                logger.warning(f"Invite from {i['AccountId']} is not the expected master. Not gonna accept it, wouldn't be prudent.")
                continue
            elif args.actually_do_it is True:
                logger.info(f"Accepting invitation {i['InvitationId']} from {args.MasterId} for {detector_id} in {region}")
                accept_invitation(guardduty_client, region, detector_id, args.MasterId, i['InvitationId'])
            else:
                logger.info(f"Need to accept invitation {i['InvitationId']} from {args.MasterId} for {detector_id} in {region}")


def accept_invitation(guardduty_client, region, detector_id, master_id, invitation_id):
    '''Accept an invitation if it is pending'''
    response = guardduty_client.accept_invitation(
        DetectorId=detector_id,
        MasterId=master_id,
        InvitationId=invitation_id
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return(True)
    else:
        logger.error(f"Attempt to accept invitation {invitation_id} from {master_id} for {detector_id} in {region} returned {response}")
        return(False)


def enable_guarduty(guardduty_client, region):
    '''Actually perform the enabling of default ebs encryption'''
    response = guardduty_client.create_detector(
        Enable=True,
        FindingPublishingFrequency='ONE_HOUR'
    )
    if 'DetectorId' in response:
        return(response['DetectorId'])
    else:
        logger.error(f"Attempt to enable GuardDuty in {region} returned {response}")
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
    parser.add_argument("--accept-invite", dest='MasterId', help="Accept an invitation (if present) from this AccountId")

    args = parser.parse_args()

    return(args)

if __name__ == '__main__':

    args = do_args()

    # Logging idea stolen from: https://docs.python.org/3/howto/logging.html#configuring-logging
    # create console handler and set level to debug
    logger = logging.getLogger('enable-guardduty')
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