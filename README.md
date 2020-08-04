# aws-fast-fixes
Scripts to quickly fix security and compliance issues

## What's the point?

AWS has a ton of good security features, but none of them are actually enabled by default. Some (like [EBS Default Encryption](https://aws.amazon.com/blogs/aws/new-opt-in-to-default-encryption-for-new-ebs-volumes/)) are buried off in an obscure settings page off a dashboard. Others like S3 Default Encryption need to be enabled each and every time. Unless you religiously read the [AWS Blogs](https://aws.amazon.com/blogs/aws/) and [What's New](https://aws.amazon.com/about-aws/whats-new/2020/) links, you might not know they exist. And don't dare go on vacation or you'll miss something!

Why AWS Accounts aren't secure & compliant by default is beyond me. While [Shared Responsibility](https://aws.amazon.com/compliance/shared-responsibility-model/) says it's our job as AWS Customers to secure ourselves _in_ the cloud, AWS could sure do a better job on security _of_ the cloud by making these features opt-out rather than opt-in. They'd probably find themselves in fewer [El Reg articles](https://www.theregister.co.uk/Tag/aws) about cloud breaches if they did.

This repo has several scripts you can run against your account to enable all the security features (and in all the regions if the feature is regional). Running this in production could have consequences because you're opt-ing in to security rather than explicitly opting out. However that's the best AWS will give us these days. *sigh*


## Scripts in this repo

* [Enable KMS Customer Key Rotation](kms-key-rotation/README.md)
* [Disable Inactive IAM Users](inactive-iam-users/README.md)
* [Enable S3 Default Bucket Encryption](s3-bucket-default-encryption/README.md)
* [Enable Default EBS Encryption](ebs-encryption/README.md)
* [Enable GuardDuty](guardduty/README.md)
* [Enable Amazon S3 Block Public Access](s3-block-public-access/README.md)

## Installing prerequisites 

The scripts in this repo only currently only require `boto3` & `pytz`. Both [pipenv](https://pypi.org/project/pipenv/) and plain pip as well

### pipenv

```bash
pipenv install
```

### pip

```bash
pip install -r requirements.txt
```
