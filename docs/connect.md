# AWS Services Integration

The WrenchCL Connect module provides seamless integration with AWS services including RDS, S3, Lambda, and Secrets Manager. It offers unified configuration, connection pooling, SSH tunneling, and comprehensive error handling.

## Installation

The AWS functionality requires additional dependencies:

```bash
# Install with AWS support
pip install 'WrenchCL[aws]'

# Or install individual dependencies
pip install boto3 psycopg2-binary paramiko sshtunnel
```

## Overview

The Connect module consists of several key components:

- **AwsClientHub** - Centralized AWS service configuration and client management
- **RdsServiceGateway** - PostgreSQL database operations with connection pooling
- **S3ServiceGateway** - S3 object storage operations with retry logic
- **Lambda Utilities** - Lambda response handling and error management

## AwsClientHub

::: WrenchCL.Connect.AwsClientHub
    options:
      show_source: false
      heading_level: 3

### Configuration

The AwsClientHub uses a flexible configuration system that loads from:

1. Environment variables
2. `.env` files
3. Direct parameter overrides

#### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_PROFILE` | AWS credentials profile | `default` |
| `REGION_NAME` | AWS region | `us-east-1` |
| `SECRET_ARN` | RDS secret ARN | `arn:aws:secretsmanager:...` |
| `SSH_SERVER` | SSH tunnel server | `bastion.example.com` |
| `SSH_USER` | SSH username | `ec2-user` |
| `PEM_PATH` | SSH private key path | `/path/to/key.pem` |
| `PGHOST_OVERRIDE` | Database host override | `localhost` |
| `PGPORT_OVERRIDE` | Database port override | `5432` |

#### Basic Usage

```python
from WrenchCL.Connect import AwsClientHub

# Initialize with defaults
hub = AwsClientHub()

# Initialize with custom .env file
hub = AwsClientHub(env_path="/path/to/.env")

# Initialize with direct overrides
hub = AwsClientHub(
    AWS_PROFILE="production",
    REGION_NAME="us-west-2",
    SECRET_ARN="arn:aws:secretsmanager:us-west-2:123456789:secret:prod-db"
)
```

#### Service Clients

```python
# Get pre-configured service clients
s3_client = hub.s3
rds_secret = hub.secretmanager
lambda_client = hub.lambda_client

# Database connection (with secret loading)
db_connection = hub.db
db_uri = hub.db_uri

# Reload configuration at runtime
hub.reload_config(AWS_PROFILE="staging")
```

## RdsServiceGateway

::: WrenchCL.Connect.RdsServiceGateway
    options:
      show_source: false
      heading_level: 3
      members:
        - get_data
        - update_database
        - enable_file_logging
        - convert_payload

### Database Operations

#### Querying Data

```python
from WrenchCL.Connect import RdsServiceGateway

rds = RdsServiceGateway()

# Simple query
users = rds.get_data(
    "SELECT * FROM users WHERE active = %s",
    payload=(True,),
    return_dict=True
)

# Single record
user = rds.get_data(
    "SELECT * FROM users WHERE id = %s",
    payload=(user_id,),
    fetchall=False,
    return_dict=True
)

# Show query for debugging
results = rds.get_data(
    "SELECT COUNT(*) FROM orders WHERE date > %s",
    payload=("2024-01-01",),
    show_query=True
)
```

#### Updating Data

```python
# Single record insert
rds.update_database(
    "INSERT INTO users (name, email) VALUES (%s, %s)",
    payload=("John Doe", "john@example.com")
)

# Batch insert with tuples
user_data = [
    ("Alice", "alice@example.com"),
    ("Bob", "bob@example.com"),
    ("Charlie", "charlie@example.com")
]

rds.update_database(
    "INSERT INTO users (name, email) VALUES %s",
    payload=user_data
)

# DataFrame batch insert
import pandas as pd

df = pd.DataFrame({
    "name": ["David", "Eve"],
    "email": ["david@example.com", "eve@example.com"]
})

rds.update_database(
    "INSERT INTO users (name, email) VALUES %s",
    payload=df,
    column_order=["name", "email"]
)
```

#### Returning Values

```python
# Insert and return generated IDs
new_ids = rds.update_database(
    "INSERT INTO users (name, email) VALUES %s RETURNING id",
    payload=[("Frank", "frank@example.com")],
    returning=True
)
print(f"New user ID: {new_ids[0][0]}")
```

### Connection Management

#### Single Connection (Default)

```python
# Standard single-connection mode
rds = RdsServiceGateway()
```

#### Connection Pooling

```python
# Enable connection pooling for multi-threaded applications
rds = RdsServiceGateway(
    multithreaded=True,
    min_pool_size=5,
    max_pool_size=20
)

# Thread-safe operations
import threading

def worker_task(thread_id):
    # Each thread gets its own connection from the pool
    results = rds.get_data("SELECT * FROM tasks WHERE assigned_to = %s", (thread_id,))
    # Connection automatically returned to pool

threads = [threading.Thread(target=worker_task, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
```

### SSH Tunneling

For secure connections through bastion hosts:

```python
# Configure SSH tunnel in environment
export SSH_SERVER=bastion.example.com
export SSH_USER=ec2-user
export PEM_PATH=/path/to/key.pem

# RDS automatically establishes tunnel
rds = RdsServiceGateway()
# Connection routed through SSH tunnel
```

### Test Mode

```python
# Enable test mode to prevent actual database commits
rds.set_test_mode(True)

# All operations will be rolled back
rds.update_database(
    "INSERT INTO users (name) VALUES (%s)",
    payload=("Test User",),
    test_mode=True  # Or global test mode
)
```

## S3ServiceGateway

::: WrenchCL.Connect.S3ServiceGateway
    options:
      show_source: false
      heading_level: 3
      members:
        - upload_file
        - get_object
        - download_object
        - delete_object
        - move_object
        - copy_object
        - check_object_existence
        - list_objects
        - get_signed_url

### File Operations

#### Uploading Files

```python
from WrenchCL.Connect import S3ServiceGateway

s3 = S3ServiceGateway()

# Upload from file path
s3.upload_file(
    file="/path/to/document.pdf",
    bucket_name="my-bucket",
    object_key="documents/document.pdf",
    return_url=True
)

# Upload bytes
data = b"Hello, World!"
s3.upload_file(
    file=data,
    bucket_name="my-bucket", 
    object_key="data/greeting.txt"
)

# Upload base64 encoded content
import base64
encoded_data = base64.b64encode(b"Binary content")
s3.upload_file(
    file=encoded_data,
    bucket_name="my-bucket",
    object_key="data/encoded.bin"
)

# Upload file-like object
from io import BytesIO
buffer = BytesIO(b"Stream content")
s3.upload_file(
    file=buffer,
    bucket_name="my-bucket",
    object_key="streams/data.bin"
)
```

#### Downloading Files

```python
# Get object as BytesIO stream
file_stream = s3.get_object(
    bucket_name="my-bucket",
    object_key="documents/document.pdf"
)

# Use the stream
content = file_stream.read()
file_stream.seek(0)  # Reset for reuse

# Download to local file
s3.download_object(
    bucket_name="my-bucket",
    object_key="documents/document.pdf",
    local_path="/local/path/document.pdf"
)
```

#### File Management

```python
# Check if object exists
exists = s3.check_object_existence(
    bucket_name="my-bucket",
    object_key="documents/document.pdf"
)

# Get object metadata
headers = s3.get_object_headers(
    bucket_name="my-bucket", 
    object_key="documents/document.pdf"
)
print(f"Content-Type: {headers['ContentType']}")
print(f"Last Modified: {headers['LastModified']}")

# Copy object
s3.copy_object(
    src_bucket_name="source-bucket",
    src_object_key="source/file.txt",
    dst_bucket_name="dest-bucket", 
    dst_object_key="dest/file.txt"
)

# Move object (copy + delete source)
s3.move_object(
    src_bucket_name="temp-bucket",
    src_object_key="temp/file.txt",
    dst_bucket_name="permanent-bucket",
    dst_object_key="permanent/file.txt"
)

# Delete object
s3.delete_object(
    bucket_name="my-bucket",
    object_key="temporary/old-file.txt"
)
```

#### Listing and URLs

```python
# List objects with prefix
objects = s3.list_objects(
    bucket_name="my-bucket",
    prefix="documents/"
)
print(f"Found {len(objects)} documents")

# Generate signed URL for temporary access
signed_url = s3.get_signed_url(
    bucket_name="my-bucket",
    object_key="private/document.pdf",
    expiration_seconds=3600  # 1 hour
)
print(f"Temporary URL: {signed_url}")

# List all buckets
buckets = s3.list_buckets()
print(f"Available buckets: {buckets}")
```

### Automatic Retry Logic

All S3 operations include automatic retry logic with exponential backoff:

```python
# Decorated with @Retryable by default
# Will retry up to 2 times with 2-second delays
# Handles common AWS exceptions automatically

# Customize retry behavior if needed
from WrenchCL.Decorators import Retryable

@Retryable(max_retries=5, delay=3, verbose=True)
def custom_s3_operation():
    # Your S3 operations with custom retry settings
    pass
```

### Test Mode

```python
# Enable test mode to prevent actual S3 modifications
s3.set_test_mode(True)

# Operations will be logged but not executed
s3.upload_file(file_data, "bucket", "key")  # Won't actually upload
s3.delete_object("bucket", "key")  # Won't actually delete
```

## Lambda Utilities

### Response Handling

::: WrenchCL.Connect.handle_lambda_response

```python
from WrenchCL.Connect import handle_lambda_response

def lambda_handler(event, context):
    try:
        # Process the request
        result = process_request(event)
        
        # Success response
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except ValidationError as e:
        # Use handle_lambda_response for errors
        handle_lambda_response(
            code=400,
            message="Invalid request data", 
            params={
                'event': str(event),
                'context': str(context),
                'lambda_client': None
            },
            client_id=event.get('client_id'),
            entity_id=event.get('user_id')
        )
    except Exception as e:
        handle_lambda_response(
            code=500,
            message=f"Internal error: {str(e)}",
            params={
                'event': str(event),
                'context': str(context)
            }
        )
```

### Error Code Mapping

The Lambda response handler maps custom error codes to appropriate HTTP status codes:

| Custom Code | Description | HTTP Code |
|-------------|-------------|-----------|
| 400 | Validation Error | 400 |
| 401 | Unauthorized | 401 |
| 403 | Forbidden | 403 |
| 404 | Resource Not Found | 404 |
| 409 | Conflict | 409 |
| 429 | Rate Limit Exceeded | 429 |
| 500 | Internal Server Error | 500 |
| 502 | Dependency Error | 502 |
| 503 | Service Unavailable | 503 |
| 504 | Gateway Timeout | 504 |
| 550-554 | Custom Server Errors | 500 |

## Configuration Examples

### Environment File (.env)

```bash
# AWS Configuration
AWS_PROFILE=production
REGION_NAME=us-east-1
SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789:secret:prod-db-abc123

# SSH Tunnel (optional)
SSH_SERVER=bastion.example.com
SSH_PORT=22
SSH_USER=ec2-user
PEM_PATH=/home/user/.ssh/production.pem

# Database Overrides (optional)
PGHOST_OVERRIDE=localhost
PGPORT_OVERRIDE=5433

# Batch Settings
DB_BATCH_OVERRIDE=50000
```

### Programmatic Configuration

```python
from WrenchCL.Connect import AwsClientHub

# Initialize with explicit configuration
hub = AwsClientHub(
    AWS_PROFILE="staging",
    REGION_NAME="us-west-2",
    SECRET_ARN="arn:aws:secretsmanager:us-west-2:456789123:secret:staging-db",
    SSH_SERVER="staging-bastion.example.com",
    SSH_USER="ubuntu",
    PEM_PATH="/keys/staging.pem",
    DB_BATCH_OVERRIDE=10000
)

# Use with services
rds = RdsServiceGateway()  # Uses the hub configuration
s3 = S3ServiceGateway()    # Uses the hub configuration
```

## Best Practices

### Error Handling

```python
from WrenchCL.Connect import RdsServiceGateway
from WrenchCL import logger

rds = RdsServiceGateway()

try:
    results = rds.get_data(
        "SELECT * FROM users WHERE id = %s",
        payload=(user_id,),
        raise_on_error=True
    )
except Exception as e:
    logger.error("Database query failed", exc_info=True)
    # Handle error appropriately
```

### Connection Pooling

```python
# For high-throughput applications
rds = RdsServiceGateway(
    multithreaded=True,
    min_pool_size=10,      # Always maintain 10 connections
    max_pool_size=50       # Scale up to 50 under load
)

# Monitor pool usage
pool_info = rds.pool.get_stats() if rds.multithreaded else None
```

### Batch Processing

```python
# Efficient batch processing
import pandas as pd

# Process data in chunks
chunk_size = 1000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    rds.update_database(
        "INSERT INTO table (col1, col2) VALUES %s",
        payload=chunk,
        column_order=['col1', 'col2']
    )
    logger.info(f"Processed {len(chunk)} records")
```

### Resource Management

```python
# Proper resource cleanup
try:
    rds = RdsServiceGateway(multithreaded=True)
    s3 = S3ServiceGateway()
    
    # Your operations
    
finally:
    # Cleanup connections
    if hasattr(rds, 'pool') and rds.pool:
        rds.pool.closeall()
```

## Troubleshooting

### Common Issues

**Connection Timeouts:**
```python
# Check SSH tunnel configuration
import os
print(f"SSH Server: {os.getenv('SSH_SERVER')}")
print(f"SSH User: {os.getenv('SSH_USER')}")
print(f"PEM Path: {os.getenv('PEM_PATH')}")

# Test direct connection without tunnel
hub = AwsClientHub(PGHOST_OVERRIDE="direct-db-host.com")
```

**Permission Errors:**
```python
# Check AWS credentials
from WrenchCL.Connect import AwsClientHub
hub = AwsClientHub()

# Test S3 access
try:
    buckets = hub.s3.list_buckets()
    print(f"Accessible buckets: {buckets}")
except Exception as e:
    print(f"S3 access error: {e}")

# Test Secrets Manager access
try:
    secret = hub.get_secret("test-secret-arn")
    print("Secrets Manager access OK")
except Exception as e:
    print(f"Secrets Manager error: {e}")
```

**Database Connection Issues:**
```python
# Test database connectivity
try:
    rds = RdsServiceGateway()
    result = rds.get_data("SELECT 1", raise_on_error=True)
    print("Database connection OK")
except Exception as e:
    logger.error("Database connection failed", exc_info=True)
```

### Debug Mode

```python
from WrenchCL import logger

# Enable debug logging for AWS operations
logger.configure(level="DEBUG", verbose=True)

# All AWS operations will show detailed logs
rds = RdsServiceGateway()
s3 = S3ServiceGateway()
```