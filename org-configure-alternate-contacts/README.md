# Set Alternate Contacts across the Organization

This script will update all the [Alternate Contacts](https://docs.aws.amazon.com/accounts/latest/reference/manage-acct-update-contact.html) for all accounts in the organization. Per [the Boto3 Docs](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/account.html#Account.Client.put_alternate_contact):

> To use this parameter, the caller must be an identity in the organization's management account or a delegated administrator account, and the specified account ID must be a member account in the same organization. The organization must have all features enabled , and the organization must have trusted access enabled for the Account Management service, and optionally a delegated admin account assigned.


## Why?

AWS will send Security, Billing and operational alerts to the Alternate Contacts enabled on an account in addition to the root email address. These settings allow security teams and finance contacts to also get important notices from AWS

## What this script does

This script must be run from the AWS Organizations Management Account!!!

It will get a list of all accounts in the organization, then it will check to see if there is an Alternate Contact already set. If not it will update the contact.

You can update all alternate contacts (not just for accounts with no alternate contact set), by specifying the `--override` parameter

Like all Fast Fix scripts, this script will run in dry-run mode by default. To actually update the alternate contact you must specify `--actually-do-it`



## Usage

```bash
usage: configure-alternate-contact.py [-h] [--debug] [--error] [--timestamp]
                                      [--actually-do-it] [--override]
                                      --contact-type CONTACT_TYPE
                                      --contact-email CONTACT_EMAIL
                                      --contact-name CONTACT_NAME
                                      --contact-phone CONTACT_PHONE
                                      --contact-title CONTACT_TITLE

optional arguments:
  -h, --help            show this help message and exit
  --debug               print debugging info
  --error               print error info only
  --timestamp           Output log with timestamp and toolname
  --actually-do-it      Actually set the alternate contact
  --override            Override any existing setting
  --contact-type CONTACT_TYPE
                        Alternate Contact to Set (SECURITY, BILLING, OPERATIONS)
  --contact-email CONTACT_EMAIL
                        Specifies an email address for the alternate contact
  --contact-name CONTACT_NAME
                        Specifies an email address for the alternate contact
  --contact-phone CONTACT_PHONE
                        Specifies a phone number for the alternate contact.
  --contact-title CONTACT_TITLE
                        Specifies a title for the alternate contact.
```

You must specify `--actually-do-it` for the changes to be made. Otherwise the script runs in dry-run mode only.


## AWS Docs

* [PutAlternateContact API](https://docs.aws.amazon.com/accounts/latest/reference/API_PutAlternateContact.html)
* [boto3 put_alternate_contact()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/account.html#Account.Client.put_alternate_contact)
* [boto3 get_alternate_contact()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/account.html#Account.Client.get_alternate_contact)
* [boto3 list_accounts()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/organizations.html#Organizations.Client.list_accounts)



