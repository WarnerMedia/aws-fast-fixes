# Unsubscribe from Marketing Emails

AWS will send marketing promotional emails to the root email of all AWS Accounts. If you manage multiple accounts, this can be highly annoying and lead to you filtering email from AWS. Filtering email sent to the root address IS REALLY BAD, since that is also how security issues are sent.



## What the unsubscribe_all_emails.sh script does.

NOTE: This script needs to be run with profile credentials from the AWS Organizations Admin account (payer account) or from any account used for Delegated Admin (ie GuardDuty, Macie, etc). It requires the command `aws organizations list-accounts` to work.


## Usage

Just run the script. It will extract all the root email addresses for invited accounts, and issue a CURL against AWS's unsubscribe URL. AWS will rate limit you, so I've included a SLEEP.

## Credit
Credit goes to Ian Mckay ([@iann0036](https://twitter.com/iann0036)) for the idea via [this tweet](https://twitter.com/iann0036/status/1176705462940635136)