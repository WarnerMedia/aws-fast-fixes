# Cloud Trail Lookup

This script will lookup Cloud Trail Event History and find events with "AccessDenied" or "Unauthorized" errors.

## Why?

Throttling error may occur with cli commands, the rate limit is 2 per region per account, and it can't be raised upon request. That's where this script comes in handy. Keep in mind the API call uses the same quota in your account, so please keep the time window for lookup as short as possible.

## What the script does.

This script iterates through all events found by parameters and list events with "AccessDenied" or "Unauthorized" errors.

## Usage

```bash
usage: enable-lambda-log-group.py [-h] [--debug] [--error] [--timestamp]
                                        [--region REGION] [--profile PROFILE]
                                        [--actually-do-it]

optional arguments:
  -h, --help         show this help message and exit
  --debug            print debugging info
  --error            print error info only
  --timestamp        Output log with timestamp and toolname
  --minutes minutes  Minutes to look up till now, default is 30, optional
  --user             User name to look up in the events, can be email or any format shown in Event History, optional
```


## AWS Docs

* [boto3 lookup_events()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudtrail.html#CloudTrail.Client.lookup_events)



