#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import os
import logging
from datetime import datetime, timedelta
import pytz

utc=pytz.UTC

def main(args, logger):
    '''Executes the Primary Logic of the Fast Fix'''

    # If they specify a profile use it. Otherwise do the normal thing
    if args.profile:
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()

    # S3 is a global service and we can use any regional endpoint for this.
    iam_client = session.client("iam")
    for user in get_all_users(iam_client):
        username = user['UserName']

        keys = get_users_keys(iam_client, username)
        if len(keys) == 0:
            logger.debug(f"User {username} has no active keys")
            continue

        for key in keys:

            # Get the last used date
            activity_response = iam_client.get_access_key_last_used(AccessKeyId=key)
            if 'AccessKeyLastUsed' not in activity_response :
                logger.error(f"Did not get AccessKeyLastUsed for user {username} key {key}")
                continue
            if 'LastUsedDate' not in activity_response['AccessKeyLastUsed']:
                logger.debug(f"Key {key} for {username} has never been used")
                continue

            # Otherwise decide what to do
            last_used_date = activity_response['AccessKeyLastUsed']['LastUsedDate']
            utc=pytz.UTC  # We need to normalize the date & timezones
            if last_used_date > utc.localize(datetime.today() - timedelta(days=int(args.threshold))):
                # Then we are good
                logger.debug(f"Key {key} ({username}) - last used {last_used_date} is OK")
            elif args.actually_do_it is True:
                # otherwise if we're configured to fix
                logger.info(f"Disabling Key {key} for {username} - Last used {activity_response['AccessKeyLastUsed']['LastUsedDate']} in {activity_response['AccessKeyLastUsed']['Region']} for {activity_response['AccessKeyLastUsed']['ServiceName']}")
                disable_key(iam_client, key, username)
            else:
                # otherwise just report
                logger.info(f"Need to Disable Key {key} for {username} - Last used {activity_response['AccessKeyLastUsed']['LastUsedDate']} in {activity_response['AccessKeyLastUsed']['Region']} for {activity_response['AccessKeyLastUsed']['ServiceName']}")



def disable_key(iam_client, key, username):
    '''perform the key disable and check the status code'''
    response = iam_client.update_access_key(
        UserName=username,
        AccessKeyId=key,
        Status='Inactive'
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return(True)
    else:
        logger.error(f"Attempt to enable disable {key} for {username} returned {response}")
        return(False)


def get_users_keys(iam_client, username):
    '''Return Active Access keys for username'''
    keyids = []
    response = iam_client.list_access_keys(UserName=username)
    if 'AccessKeyMetadata' in response:
        for k in response['AccessKeyMetadata']:
            if k['Status'] == "Active":
                keyids.append(k['AccessKeyId'])
    return(keyids)


def get_all_users(iam_client):
    '''Return an array of all IAM Users. '''
    users = []
    response = iam_client.list_users()
    while 'IsTruncated' in response and response['IsTruncated'] is True:  # Gotta Catch 'em all!
        users += response['Users']
        response = iam_client.list_users(Marker=response['Marker'])
    users += response['Users']
    return(users)


def do_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="print debugging info", action='store_true')
    parser.add_argument("--error", help="print error info only", action='store_true')
    parser.add_argument("--timestamp", help="Output log with timestamp and toolname", action='store_true')
    parser.add_argument("--profile", help="Use this CLI profile (instead of default or env credentials)")
    parser.add_argument("--actually-do-it", help="Actually Perform the action", action='store_true')
    parser.add_argument("--threshold", help="Number of days of inactivity to disable. Default is 90 days", default=90)

    args = parser.parse_args()

    return(args)

if __name__ == '__main__':

    args = do_args()

    # Logging idea stolen from: https://docs.python.org/3/howto/logging.html#configuring-logging
    # create console handler and set level to debug
    logger = logging.getLogger('disable-inactive-keys')
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