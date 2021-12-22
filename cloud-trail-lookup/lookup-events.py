#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import os
import logging
import time
from datetime import datetime as dt, timedelta, time
import json

# python3 ./lookup-events.py --debug --minutes 10 --user email@warnermedia.com

def get_arg_minutes(args):
    minutes_to_lookup = 30
    try:
        if args.minutes:
            minutes_to_lookup = int(args.minutes)
    except Exception as e:
        logger.info("An exception occurred converting arg minutes: ", e) 
    logger.info(f"minutes to look up: {minutes_to_lookup}")
    return minutes_to_lookup

def get_arg_user(args):
    user_to_lookup = ""
    if args.user:
        user_to_lookup = args.user
    logger.info(f"user to look up: {user_to_lookup}")
    return user_to_lookup

def main(args, logger):
    # just want to quickly run "aws cloudtrail lookup-events" without ThrottleException
    # only care about us-east-1, use default profile
    client = boto3.client('cloudtrail')

    minutes_to_lookup = get_arg_minutes(args)
    user_to_lookup = get_arg_user(args)

    lastHourDateTime = dt.utcnow() - timedelta(minutes=minutes_to_lookup)
    now = dt.utcnow()
    startTime = lastHourDateTime
    endTime = now

    logger.info(f"start Time: {startTime}")
    logger.info(f"end time: {endTime}")

    maxResult = 200
    events_found = []
    # no NextToken at first
    event_arg = {"StartTime": startTime, "EndTime": endTime, "MaxResults": maxResult}
    if user_to_lookup:
        event_arg["LookupAttributes"] = [{
            'AttributeKey': 'Username',
            'AttributeValue': user_to_lookup
        }]
    response = client.lookup_events(**event_arg)

    # process response, add to events array
    events_found = events_found + search_events(response["Events"])

    if "NextToken" in response:
        nextToken = response["NextToken"]

        logger.debug(nextToken)

        while nextToken:
            event_arg["NextToken"] = nextToken
            response = client.lookup_events(**event_arg)
            
            events_found = events_found + search_events(response["Events"])

            if "NextToken" in response:
                nextToken = response["NextToken"]
                logger.debug(nextToken)
            else:
                # loop ends
                nextToken = ""
    logger.info(f"events_found: {events_found}")
    logger.info(f"{len(events_found)} events found")
    return events_found


def search_events(events):
    # list events with error code of "accessdenied" or "unauthorized"
    filtered = []
    for event in events:
        event_detail_str = event["CloudTrailEvent"]
        event_detail = json.loads(event_detail_str)
        if "errorCode" in event_detail:
            if event_detail["errorCode"].lower() == "accessdenied" or event_detail["errorCode"].lower() == "unauthorized":
                filtered.append(event)
    return filtered


def do_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug", help="print debugging info", action='store_true')
    parser.add_argument(
        "--error", help="print error info only", action='store_true')
    parser.add_argument(
        "--timestamp", help="Output log with timestamp and toolname", action='store_true')
    parser.add_argument(
        "--minutes", help="minutes to look up till now")
    parser.add_argument(
        "--user", help="user name to look up")

    args = parser.parse_args()

    return (args)


if __name__ == '__main__':

    args = do_args()

    # create console handler and set level to debug
    logger = logging.getLogger('cloud-trail-lookup-events')
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
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
