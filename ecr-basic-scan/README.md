# ECR Registry Basic Scan

This script will lookup ECR repos and images given an ECR registry id, then trigger scan manually for each image given that the registry scan configuration is set to Basic scan.

## Why?

Manual scans using enhanced scanning isn’t supported. 
When continuous scanning is enabled for a repository, if an image hasn’t been updated in the past 30 days based on the image push timestamp, then continuous scanning is suspended for that image.


## What the script does not do
Registry scan configuration as Basic scan needs to be set up ahead of time. Note that as of this writing, basic scanning is not able to detect the log4j 2 vulnerability.


## Errors
The following error could occur as an image can only be scanned once per day:
"An error occurred (LimitExceededException) when calling the StartImageScan operation: The scan quota per image has been exceeded. Wait and try again."

## Usage

```bash
usage: automate-manual-scan.py [-h] [--debug] [--error] [--timestamp]
                                        [--registry-id]
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

* [boto3 ECR](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecr.html)



