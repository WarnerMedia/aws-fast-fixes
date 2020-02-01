# S3 Bucket Default Encryption

This script will enable S3 Bucket Default Encryption (using AWS Managed Keys) on all S3 buckets with out it enabled in your account.

## Why?

*Amazon S3 default encryption provides a way to set the default encryption behavior for an S3 bucket. You can set default encryption on a bucket so that all new objects are encrypted when they are stored in the bucket. The objects are encrypted using server-side encryption with either Amazon S3-managed keys (SSE-S3) or customer master keys (CMKs) stored in AWS Key Management Service (AWS KMS)* ([source](https://docs.aws.amazon.com/AmazonS3/latest/dev/bucket-encryption.html)).


## What the script does.

This script will generate a list of all the S3 Buckets in your account. If the Default Encryption is not set, and no bucket policies with encryption conditions exist, this script will enable Default Encryption with Amazon S3-Managed Keys (SSE-S3).

**CAUTION!!** AWS provides the following warning when enabling Default Encryption: *Amazon S3 evaluates and applies bucket policies before applying bucket encryption settings. Even if you enable bucket encryption settings, your PUT requests without encryption information will be rejected if you have bucket policies to reject such PUT requests. Check your bucket policy and modify it if required.*

This script looks for the following conditions in the bucket policy and will skip over any bucket that contains any one of these:
* `x-amz-server-side-encryption`
* `x-amz-server-side-encryption-aws-kms-key-id`

Reference: https://docs.aws.amazon.com/AmazonS3/latest/dev/amazon-s3-policy-keys.html#AvailableKeys-iamV2

Skipped buckets are prefixed with WARNING


## Usage

```bash
usage: enable-s3-bucket-default-encryption.py [-h] [--debug] [--error] [--timestamp]
                                  [--region REGION] [--actually-do-it]

optional arguments:
  -h, --help        show this help message and exit
  --debug           print debugging info
  --error           print error info only
  --timestamp       Output log with timestamp and toolname
  --profile PROFILE  Use this CLI profile (instead of default or env credentials)
  --actually-do-it  Actually Perform the action
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.


## AWS Docs

* [Amazon S3 Default Encryption for S3 Buckets](https://docs.aws.amazon.com/AmazonS3/latest/dev/bucket-encryption.html)
* [PutBucketEncryption API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutBucketEncryption.html)
* [boto3 list_buckets()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_buckets)
* [boto3 get_bucket_encryption()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.get_bucket_encryption)
* [boto3 put_bucket_encryption()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_bucket_encryption)


