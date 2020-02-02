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

        if 'PasswordLastUsed' not in user:
            logger.debug(f"User {username} has no PasswordLastUsed")
            continue

        # We need to make sure a Login Profile still exists (the PasswordLastUsed can be set on a removed LoginProfile)
        if not has_login_profile(iam_client, username):
            logger.debug(f"User {username} no longer has a LoginProfile")
            continue

        last_login = user['PasswordLastUsed']
        utc=pytz.UTC  # We need to normalize the date & timezones
        if last_login > utc.localize(datetime.today() - timedelta(days=int(args.threshold))):
            # Then we are good
            logger.debug(f"{username} - last login {last_login} is OK")
        elif args.actually_do_it is True:
            # otherwise if we're configured to fix
            logger.info(f"Disabling Login for {username} - Last used {last_login}")
            disable_login(iam_client, username)
        else:
            # otherwise just report
            logger.info(f"Need to Disable login for {username} - Last used {last_login}")


def has_login_profile(iam_client, username):
    '''Confirms the user still has a login profile before we attempt to remove it'''
    try:
        response = iam_client.get_login_profile(UserName=username)
        if 'LoginProfile' in response:
            return(True)
    except ClientError as e:
        if e.response['Error']['Code'] == "NoSuchEntity":
            return(False)
        else:
            raise


def disable_login(iam_client, username):
    '''perform the key disable and check the status code'''
    response = iam_client.delete_login_profile(UserName=username)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return(True)
    else:
        logger.error(f"Attempt to enable LoginProfile for {username} returned {response}")
        return(False)


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