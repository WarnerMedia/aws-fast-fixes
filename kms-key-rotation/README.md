# kms-key-rotation

This script will enable annual key rotation on all AWS Customer Managed Keys in your account.

## Why?

AWS Key rotation triggers AWS to create a new backing-key for your CMK. These backing-keys are the actual bits used for the encryption and decryption with KMS CMKs. Old backing-keys are not removed, and no data or envelop keys that were encrypted with the old backing-key are re-encrypted.

This exists to make old-school on-prem crypto-compliance folks happy. However security tools and security policies often ding account owners for not having this set.

## What the script does.

This script will iterate through all your regions and attempt to list all your keys. If you have permission to the key (ie it is not locked down to a specific principal), it will issue the [EnableKeyRotation API](https://docs.aws.amazon.com/kms/latest/APIReference/API_EnableKeyRotation.html) call.

## AWS Docs

* [Rotating Customer Master Keys](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)
* [EnableKeyRotation API](https://docs.aws.amazon.com/kms/latest/APIReference/API_EnableKeyRotation.html)
* [boto3 enable_key_rotation()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#KMS.Client.enable_key_rotation)
* [boto3 list_keys()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#KMS.Client.list_keys)
* [boto3 get_key_rotation_status()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#KMS.Client.get_key_rotation_status)


