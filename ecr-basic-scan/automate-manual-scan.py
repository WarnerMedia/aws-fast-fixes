#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
import os
import logging
import time
from datetime import datetime as dt, timedelta, time
import json

# Assume basic scan setting has been set up in the private registry, otherwise the script throws error 
# Trigger manual scan for all images in a repos, catch and display if any errors for each, continue with loop
# python3 automate-manual-scan.py --registry-id <accountNumberForPrivateRegistry>
def start_image_scan(client, registry_id, repo_name, image_digest):
    try:
        response = client.start_image_scan(
            registryId=registry_id,
            repositoryName=repo_name,
            imageId={
                'imageDigest': image_digest
            }
        )
        logger.info(response)
    except Exception as e:
        logger.info(f'An exception occurred starting image scan in repo {repo_name} with image digest {image_digest}') 


def list_ecr_repos(client, registry_id):
    MAX_RESULT = 100
    repo_names = []
    payload = {
        'registryId': registry_id,
        'maxResults': MAX_RESULT
    }
    try:
        response = client.describe_repositories(**payload)
        repos = response['repositories']
        repo_names = [repo['repositoryName'] for repo in repos]
        if "NextToken" in response:
            nextToken = response["NextToken"]

            while nextToken:
                payload["NextToken"] = nextToken
                response = client.describe_repositories(**payload)
                repo_names = repo_names + [repo['repositoryName'] for repo in repos]

                if "NextToken" in response:
                    nextToken = response["NextToken"]
                    logger.debug(nextToken)
                else:
                    # loop ends
                    nextToken = ""
        return repo_names
    except Exception as e:
        logger.info(f'An exception occurred in list_ecr_repos') 
    

"""
    returned array in this format
    [
        {
            'imageDigest': 'string',
            'imageTag': 'string'
        },
    ],
"""
def list_images(client, registry_id, repo_name):
    MAX_RESULT = 100
    image_ids = []
    payload = {
                'registryId': registry_id,
                'repositoryName': repo_name,
                'maxResults': MAX_RESULT,
                "filter": {
                    'tagStatus': 'ANY'
                    }
                }
    try:
        response = client.list_images(**payload)
        image_ids = response['imageIds']
        if "NextToken" in response:
            nextToken = response["NextToken"]

            while nextToken:
                payload["NextToken"] = nextToken
                response = client.list_images(**payload)
                image_ids = image_ids + response['imageIds']
                
                if "NextToken" in response:
                    nextToken = response["NextToken"]
                    logger.debug(nextToken)
                else:
                    # loop ends
                    nextToken = ""
        return image_ids
    except Exception as e:
        logger.info(f'An exception occurred listing images in repo {repo_name}') 


def main(args, logger):
    # use default profile
    client = boto3.client('ecr')
    logger.info(f'registry_id: {args.registry_id}')
    repo_names = list_ecr_repos(client, args.registry_id)
    for repo_name in repo_names:
        logger.info(f'repo_name: {repo_name}')
        image_ids = list_images(client, args.registry_id, repo_name)
        for image_id in image_ids:
            if args.actually_do_it is True:
                start_image_scan(client, args.registry_id, repo_name, image_id['imageDigest'])


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
        "--actually-do-it", help="Actually Perform the action", action='store_true')
    parser.add_argument(
        "--registry-id", help="private registry id (account number)")
    
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
