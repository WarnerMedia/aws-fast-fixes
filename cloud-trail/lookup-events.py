#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import os
import logging
import time
from datetime import datetime as dt, timedelta
import json

# python3 ./lookup-events.py --debug


def main(args, logger):
    # just want to quickly run "aws cloudtrail lookup-events" without ThrottleException
    # only care about us-east-1, use default profile
    client = boto3.client('cloudtrail')

    lastHourDateTime = dt.now() - timedelta(hours=1)
    now = dt.now()
    maxResult = 200
    events_found = []
    response = client.lookup_events(
        LookupAttributes=[
            {
                'AttributeKey': 'EventName',
                'AttributeValue': 'GetTopicAttributes'
            },
        ],
        StartTime=lastHourDateTime,
        EndTime=now,
        MaxResults=maxResult
        # no NextToken at first
    )
    # process response, add to events array
    events_found.append(search_events(response["Events"]))

    if "NextToken" in response:
        nextToken = response["NextToken"]

        print(nextToken)

        while nextToken:
            response = client.lookup_events(
                LookupAttributes=[
                    {
                        'AttributeKey': 'EventName',
                        'AttributeValue': 'GetTopicAttributes'
                    },
                ],
                StartTime=lastHourDateTime,
                EndTime=now,
                MaxResults=maxResult,
                NextToken=nextToken
            )
            events_found.append(search_events(response["Events"]))

            if "NextToken" in response:
                nextToken = response["NextToken"]
                print(nextToken)
            else:
                # loop ends
                nextToken = ""
    print(events_found)
    return events_found


def search_events(events):
    # list events with error code of "accessdenied" or "unauthorized"
    events = []
    for event in events:
        event_detail_str = event["CloudTrailEvent"]
        event_detail = json.loads(event_detail_str)
        if "errorCode" in event_detail:
            if event_detail["errorCode"].lower() == "accessdenied" or event_detail["errorCode"].lower() == "unauthorized":
                events.append(event)
    return events


def do_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug", help="print debugging info", action='store_true')
    parser.add_argument(
        "--error", help="print error info only", action='store_true')
    parser.add_argument(
        "--timestamp", help="Output log with timestamp and toolname", action='store_true')

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
