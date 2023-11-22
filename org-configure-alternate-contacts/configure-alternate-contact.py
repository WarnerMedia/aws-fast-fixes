#!/usr/bin/env python3

from botocore.exceptions import ClientError
import boto3
import datetime
import json
import os
import time

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


VALID_TYPES=['BILLING', 'SECURITY', 'OPERATIONS']


def main(args, logger):

    if args.contact_type not in VALID_TYPES:
        logger.critical(f"Specified Contact Type {args.contact_type} is not one of the valid types: {' '.join(VALID_TYPES)}")
        exit(1)

    account_list = get_organization_accounts(args)
    logger.info(f"Found {len(account_list)} accounts in this organization")

    client = boto3.client('account')
    for a in account_list:
        account_id = a['Id']
        # if account_id == "373051592877":
        #     continue

        current_contact = get_alternate_contact(a, client, args)
        logger.debug(f"Account {a['Name']} ({account_id}) has contact type {args.contact_type} of {current_contact}")
        if args.actually_do_it and args.override:
            update_account_contact(a, client, args)
        elif current_contact is None and args.actually_do_it:
            update_account_contact(a, client, args)
        elif current_contact is None:
            logger.info(f"No alternate contact of type {args.contact_type} set for {a['Name']} ({account_id}) ")
        else:
            logger.info(f"Account {a['Name']} ({account_id}) already has contact type {args.contact_type} set to {current_contact['Name']} - {current_contact['EmailAddress']}")


def get_alternate_contact(a, client, args):
    try:
        if a['Id'] == a['Arn'].split(':')[4]:
            response = client.get_alternate_contact(AlternateContactType=args.contact_type)
        else:
            response = client.get_alternate_contact(
                AccountId=a['Id'],
                AlternateContactType=args.contact_type
            )
        current_contact = response['AlternateContact']
        return(current_contact)
    except ClientError as e:
        if e.response['Error']['Code'] == "ResourceNotFoundException":
            return(None)
        else:
            raise


def update_account_contact(a, client, args):
    account_id = a['Id']
    try:
        if a['Id'] == a['Arn'].split(':')[4]:
            response = client.put_alternate_contact(
                AlternateContactType=args.contact_type,
                EmailAddress=args.contact_email,
                Name=args.contact_name,
                PhoneNumber=args.contact_phone,
                Title=args.contact_title
            )
        else:
            response = client.put_alternate_contact(
                AccountId=account_id,
                AlternateContactType=args.contact_type,
                EmailAddress=args.contact_email,
                Name=args.contact_name,
                PhoneNumber=args.contact_phone,
                Title=args.contact_title
            )
        logger.info(f"Set Alternate Contact {args.contact_type} for {a['Name']} ({account_id}) ")
    except ClientError as e:
        logger.error(f"Error Setting Alternate Contact Type {args.contact_type} for {account_id}: {e}")


def get_organization_accounts(args):
    logger.info("Fetching account list...")
    org_client = boto3.client('organizations')
    try:

        output = []
        response = org_client.list_accounts(MaxResults=20)
        while 'NextToken' in response:
            output = output + response['Accounts']
            time.sleep(1)
            response = org_client.list_accounts(MaxResults=20, NextToken=response['NextToken'])

        output = output + response['Accounts']
        return(output)
    except ClientError as e:
        if e.response['Error']['Code'] == 'AWSOrganizationsNotInUseException':
            # This is a standalone account
            logger.critical("This script is intended only for AWS Organizations. Organizations is not fully enabled for this account. Aborting...")
            exit(1)
        # This is what we get if we're a child in an organization, but not inventorying the payer
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            logger.critical("This script must be run in the AWS Organizations Management Account. Aborting...")
            exit(1)
        else:
            raise


def do_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="print debugging info", action='store_true')
    parser.add_argument("--error", help="print error info only", action='store_true')
    parser.add_argument("--timestamp", help="Output log with timestamp and toolname", action='store_true')
    parser.add_argument("--actually-do-it", help="Actually set the alternate contact", action='store_true')
    parser.add_argument("--override", help="Override any existing setting", action='store_true')
    parser.add_argument("--contact-type", help="Alternate Contact to Set (SECURITY, BILLING, OPERATIONS)", required=True)
    parser.add_argument("--contact-email", help="Specifies an email address for the alternate contact", required=True)
    parser.add_argument("--contact-name", help="Specifies an email address for the alternate contact", required=True)
    parser.add_argument("--contact-phone", help="Specifies a phone number for the alternate contact.", required=True)
    parser.add_argument("--contact-title", help="Specifies a title for the alternate contact.", required=True)




    args = parser.parse_args()

    return(args)

if __name__ == '__main__':

    args = do_args()

    # Logging idea stolen from: https://docs.python.org/3/howto/logging.html#configuring-logging
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    if args.error:
        logger.setLevel(logging.ERROR)
    elif args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # create formatter
    if args.timestamp:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        formatter = logging.Formatter('%(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    # # Sanity check region
    # if args.region:
    #     os.environ['AWS_DEFAULT_REGION'] = args.region

    # if 'AWS_DEFAULT_REGION' not in os.environ:
    #     logger.error("AWS_DEFAULT_REGION Not set. Aborting...")
    #     exit(1)

    try:
        main(args, logger)
    except KeyboardInterrupt:
        exit(1)