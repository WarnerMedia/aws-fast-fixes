# S3 Block Public Access

This script will enable Block Public Access on all S3 buckets in your account.

## Why?

Public Exposed S3 Buckets are the primary way data beaches occur in AWS. AWS has traditionally done a poor job helping it's customers understand the implications of Bucket Policies, Bucket ACLs and Object ACLs. After numerous data breaches tarnished its image, AWS created the Block Public Access option which can be applied to an S3 Bucket. [Block Public Access](https://aws.amazon.com/s3/features/block-public-access/) is a security control that overrides all Bucket Policies and Bucket and Object ACLs.


## What the script does.

This script will generate a list of all the S3 Buckets in your account. If the Block Public Access is not set, and no bucket policies with public conditions exist, this script will enable Block Public Access.

**CAUTION!!** Blocking Public Access on S3 buckets that are service content can cause a production issue. Unless you're really sure what you're doing, we recommend using the --output-script FILENAME option to write out the commands to be executed. You can then select the S3 Buckets you know you want to enable Block Public Access on.

Skipped buckets are prefixed with WARNING


## Usage

```bash
usage: enable-s3-block-public-access.py [-h] [--debug] [--error] [--timestamp]
                                        [--profile PROFILE] [--actually-do-it]
                                        [--output-script FILENAME]

optional arguments:
  -h, --help            show this help message and exit
  --debug               print debugging info
  --error               print error info only
  --timestamp           Output log with timestamp and toolname
  --profile PROFILE     Use this CLI profile (instead of default or env credentials)
  --actually-do-it      Actually Perform the action
  --output-script FILENAME
                        Write CLI Commands to FILENAME for later execution
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.

You can specify `--output-script FILENAME` to produce a shell script with the AWS CLI Commands to fix all the buckets. You can then modify the script before execution.


## AWS Docs

* [Amazon S3 Block Public Access](https://aws.amazon.com/s3/features/block-public-access/) Feature Docs
* [PutPublicAccessBlock](https://docs.aws.amazon.com/goto/WebAPI/s3-2006-03-01/PutPublicAccessBlock) API
* [boto3 list_buckets()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_buckets)
* [boto3 get_public_access_block()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.get_public_access_block)
* [boto3 put_public_access_block()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_public_access_block)
* [boto3 get_bucket_acl()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.get_bucket_acl)
* [boto3 get_bucket_policy()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.get_bucket_policy)

### Settings for Public Access Block
This description is taken from the [Boto3 Docs for put_public_access_block()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_public_access_block)

* BlockPublicAcls (boolean) --

  Specifies whether Amazon S3 should block public access control lists (ACLs) for this bucket and objects in this bucket. Setting this element to TRUE causes the following behavior:

  * PUT Bucket acl and PUT Object acl calls fail if the specified ACL is public.
  * PUT Object calls fail if the request includes a public ACL.
  * PUT Bucket calls fail if the request includes a public ACL.

  Enabling this setting doesn't affect existing policies or ACLs.

* IgnorePublicAcls (boolean) --

  Specifies whether Amazon S3 should ignore public ACLs for this bucket and objects in this bucket. Setting this element to TRUE causes Amazon S3 to ignore all public ACLs on this bucket and objects in this bucket.

  Enabling this setting doesn't affect the persistence of any existing ACLs and doesn't prevent new public ACLs from being set.

* BlockPublicPolicy (boolean) --

  Specifies whether Amazon S3 should block public bucket policies for this bucket. Setting this element to TRUE causes Amazon S3 to reject calls to PUT Bucket policy if the specified bucket policy allows public access.

  Enabling this setting doesn't affect existing bucket policies.

* RestrictPublicBuckets (boolean) --

  Specifies whether Amazon S3 should restrict public bucket policies for this bucket. Setting this element to TRUE restricts access to this bucket to only AWS services and authorized users within this account if the bucket has a public policy.

  Enabling this setting doesn't affect previously stored bucket policies, except that public and cross-account access within any public bucket policy, including non-public delegation to specific accounts, is blocked.
