
# SSH Tunnel
better logging for when pem path is missing

**Current**
```python
b'{"ARN":"arn:aws:secretsmanager:us-east-1:293975147414:secret:rds-masteruser-qa-Rd7t6c","CreatedDate":1.640706119443E9,"Name":"rds-masteruser-qa","SecretString":"{\\"username\\":\\"masteruser\\",\\"password\\":\\"fvU7216ckUcmcd1O3RxQ\\",\\"engine\\":\\"postgres\\",\\"host\\":\\"qa-wrench-ai.ce5sivkxtgbs.us-east-1.rds.amazonaws.com\\",\\"port\\":5432,\\"dbname\\":\\"enricher\\",\\"dbInstanceIdentifier\\":\\"qa-wrench-ai\\"}","VersionId":"eead7b3b-9884-4111-87b5-ededac3b7ad9","VersionStages":["AWSCURRENT"]}'
DEBUG   : [R-B29UP2-1106] hooks.py:_emit:238  | 2024-08-27 06:03:18 | Event needs-retry.secrets-manager.GetSecretValue: calling handler <botocore.retryhandler.RetryHandler object at 0x000001F8D0372E10>
DEBUG   : [R-B29UP2-1106] retryhandler.py:__call__:211  | 2024-08-27 06:03:18 | No retry needed.
ERROR   : [R-B29UP2-1106] sshtunnel.py:_connect_to_gateway:1427 | 2024-08-27 06:03:19 | Could not open connection to gateway
ERROR   : [R-B29UP2-1106] AwsClientHub.py:_init_rds_client:213  | 2024-08-27 06:03:19 | An exception occurred when initializing connection to DB: Could not establish session to SSH gateway
ERROR   : [R-B29UP2-1106] local_test.py:<module>:137  | 2024-08-27 06:03:19 | An error occurred while running lambda: Could not establish session to SSH gateway
```

# Handle Lambda Response
Add docstring documentation of the different numerical return codes and what they mean