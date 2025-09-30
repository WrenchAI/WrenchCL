# AWS Connect

WrenchCL Connect provides AWS service integrations. **Requires additional dependencies.**

## Installation

```bash
# Install AWS dependencies
pip install WrenchCL[aws]

# Or install manually
pip install boto3 psycopg2-binary paramiko sshtunnel
```

Without these dependencies, importing Connect modules will raise helpful error messages.

## Import Structure

```python
# Will fail if AWS dependencies not installed
from WrenchCL.Connect import AwsClientHub, RdsServiceGateway, S3ServiceGateway
from WrenchCL.Connect import handle_lambda_response
```

## AwsClientHub

Centralized AWS client management with configuration loading:

```python
from WrenchCL.Connect import AwsClientHub

# Basic initialization
hub = AwsClientHub()

# With custom .env file
hub = AwsClientHub(env_path="/path/to/.env")

# With direct overrides
hub = AwsClientHub(
        AWS_PROFILE="production",
        REGION_NAME="us-west-2",
        SECRET_ARN="arn:aws:secretsmanager:..."
        )

# Access AWS clients
s3_client = hub.s3
secrets_client = hub.secretmanager
lambda_client = hub.lambda_client

# Database access (loads RDS secrets)
db_connection = hub.db
db_uri = hub.db_uri
```

### Configuration

Environment variables (or .env file):

```bash
AWS_PROFILE=default
REGION_NAME=us-east-1
SECRET_ARN=arn:aws:secretsmanager:...
SSH_SERVER=bastion.example.com
SSH_USER=ec2-user
PEM_PATH=/path/to/key.pem
PGHOST_OVERRIDE=localhost
PGPORT_OVERRIDE=5432
```

## RdsServiceGateway

PostgreSQL database operations with connection pooling:

```python
from WrenchCL.Connect import RdsServiceGateway

# Single connection (default)
rds = RdsServiceGateway()

# Connection pooling for multi-threaded apps
rds = RdsServiceGateway(
        multithreaded=True,
        min_pool_size=5,
        max_pool_size=20
        )
```

### Database Operations

```python
# Query data
users = rds.get_data(
        "SELECT * FROM users WHERE active = %s",
        payload=(True,),
        return_dict=True
        )

# Single record
user = rds.get_data(
        "SELECT * FROM users WHERE id = %s",
        payload=(user_id,),
        fetchall=False
        )

# Update operations
rds.update_database(
        "INSERT INTO users (name, email) VALUES (%s, %s)",
        payload=("John", "john@example.com")
        )

# Batch operations
user_data = [("Alice", "alice@example.com"), ("Bob", "bob@example.com")]
rds.update_database(
        "INSERT INTO users (name, email) VALUES %s",
        payload=user_data
        )

# With DataFrame
import pandas as pd

df = pd.DataFrame({"name": ["Dave"], "email": ["dave@example.com"]})
rds.update_database(
        "INSERT INTO users (name, email) VALUES %s",
        payload=df,
        column_order=["name", "email"]
        )
```

### Test Mode

```python
# Prevent actual database commits
rds.set_test_mode(True)
rds.update_database("INSERT INTO ...", test_mode=True)  # Rolls back
```

## S3ServiceGateway

S3 operations with automatic retry logic:

```python
from WrenchCL.Connect import S3ServiceGateway

s3 = S3ServiceGateway()

# Upload files
s3.upload_file("/path/to/file.jpg", "my-bucket", "images/file.jpg")
s3.upload_file(byte_data, "my-bucket", "data/file.bin")

# Download
file_stream = s3.get_object("my-bucket", "images/file.jpg")
s3.download_object("my-bucket", "images/file.jpg", "/local/path.jpg")

# File operations
exists = s3.check_object_existence("my-bucket", "images/file.jpg")
s3.copy_object("src-bucket", "src/key", "dst-bucket", "dst/key")
s3.move_object("temp-bucket", "temp/key", "perm-bucket", "perm/key")
s3.delete_object("my-bucket", "old/file.jpg")

# List and URLs
objects = s3.list_objects("my-bucket", prefix="images/")
signed_url = s3.get_signed_url("my-bucket", "private/file.pdf", expiration_seconds=3600)
```

### Test Mode

```python
# Prevent actual S3 operations
s3.set_test_mode(True)
s3.upload_file(data, "bucket", "key")  # Won't actually upload
```

## Lambda Utilities

Error handling for AWS Lambda functions:

```python
from WrenchCL.Connect import handle_lambda_response


def lambda_handler(event, context):
    try:
        # Process request
        result = process_request(event)
        return {
                'statusCode': 200,
                'body': json.dumps(result)
                }
    except ValidationError:
        handle_lambda_response(
                code=400,
                message="Invalid request",
                params={
                        'event': str(event),
                        'context': str(context)
                        }
                )
    except Exception as e:
        handle_lambda_response(
                code=500,
                message=f"Internal error: {str(e)}",
                params={'event': str(event), 'context': str(context)}
                )
```

Error codes map to appropriate HTTP status codes (400-500 range).

## SSH Tunneling

For secure database connections through bastion hosts:

```bash
# Environment variables
export SSH_SERVER=bastion.example.com
export SSH_USER=ec2-user  
export PEM_PATH=/path/to/key.pem

# Or SSH password
export SSH_PASSWORD=secret
```

The RdsServiceGateway automatically establishes SSH tunnels when configured.

## Configuration Examples

### .env File

```bash
AWS_PROFILE=production
REGION_NAME=us-east-1
SECRET_ARN=arn:aws:secretsmanager:us-east-1:123:secret:db
SSH_SERVER=bastion.example.com
SSH_USER=ec2-user
PEM_PATH=/home/user/.ssh/prod.pem
DB_BATCH_OVERRIDE=5000
```

### Programmatic

```python
hub = AwsClientHub(
        AWS_PROFILE="staging",
        SECRET_ARN="arn:aws:secretsmanager:...",
        SSH_SERVER="staging-bastion.com",
        PEM_PATH="/keys/staging.pem"
        )

# Services automatically use this configuration
rds = RdsServiceGateway()
s3 = S3ServiceGateway()
```

## Error Handling

All operations include proper error handling and logging:

```python
try:
    results = rds.get_data("SELECT * FROM users", raise_on_error=True)
except Exception as e:
    logger.error("Database query failed", exc_info=True)

# S3 operations have built-in retry logic
s3.upload_file(data, "bucket", "key")  # Automatically retries on failure
```

## Dependency Requirements

The Connect module requires:

- `boto3` - AWS SDK
- `psycopg2-binary` - PostgreSQL adapter
- `paramiko` - SSH client
- `sshtunnel` - SSH tunneling

Install with `pip install WrenchCL[aws]` or install packages individually.