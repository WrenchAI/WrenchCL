# Connect Module Documentation

The Connect module provides production-ready AWS service integrations with automatic configuration, connection pooling, and intelligent error handling.

## Overview

- **AwsClientHub**: Centralized AWS client management with automatic configuration
- **RdsServiceGateway**: PostgreSQL database operations with connection pooling
- **S3ServiceGateway**: S3 operations with retry logic and validation
- **handle_lambda_response**: Standardized Lambda response handling

## AwsClientHub

Singleton manager for AWS clients and secrets with optional SSH tunneling.

### Features
- **Automatic Configuration**: Loads from .env files, environment variables, and kwargs
- **Secret Management**: Integrates with AWS Secrets Manager
- **SSH Tunneling**: Secure database connections through bastion hosts
- **Lazy Loading**: Clients are created only when needed
- **Thread Safety**: Safe for concurrent applications

### Quick Start

```python
from WrenchCL.Connect import AwsClientHub

# Initialize with automatic configuration
hub = AwsClientHub()

# Access AWS services
s3_client = hub.s3
rds_client = hub.db
secrets_client = hub.secretmanager
lambda_client = hub.lambda_client

# Get database URI
db_uri = hub.db_uri
```

### Configuration

The hub loads configuration from multiple sources in order:

1. **.env file** (if provided)
2. **Environment variables**
3. **Keyword arguments** (highest priority)

#### Environment Variables

```bash
# Core AWS Configuration
AWS_PROFILE=my-profile
REGION_NAME=us-east-1
SECRET_ARN=arn:aws:secretsmanager:region:account:secret:name

# SSH Tunnel Configuration (optional)
SSH_SERVER=bastion.example.com
SSH_PORT=22
SSH_USER=ec2-user
SSH_PASSWORD=password
# OR
PEM_PATH=/path/to/key.pem

# Connection Overrides (optional)
PGHOST_OVERRIDE=localhost
PGPORT_OVERRIDE=5432
DB_BATCH_OVERRIDE=5000
```

#### Programmatic Configuration

```python
hub = AwsClientHub(
    env_path=".env.production",
    AWS_PROFILE="production",
    REGION_NAME="us-west-2",
    SECRET_ARN="arn:aws:secretsmanager:us-west-2:123:secret:db-prod"
)

# Reload configuration at runtime
hub.reload_config(
    AWS_PROFILE="staging",
    SECRET_ARN="arn:aws:secretsmanager:us-west-2:123:secret:db-staging"
)
```

### Advanced Usage

#### Custom Secret Retrieval
```python
# Get specific secret
user_secret = hub.get_secret("arn:aws:secretsmanager:region:account:secret:user-creds")

# Returns parsed JSON dict or raw string
if isinstance(user_secret, dict):
    username = user_secret["username"]
    password = user_secret["password"]
```

#### SSH Tunnel Example
```python
# Automatic SSH tunnel when all SSH config is provided
hub = AwsClientHub(
    SSH_SERVER="bastion.company.com",
    SSH_USER="ec2-user", 
    PEM_PATH="/path/to/bastion-key.pem"
)

# Database connection automatically tunneled
db_connection = hub.db
```

---

## RdsServiceGateway

High-performance PostgreSQL gateway with connection pooling and batch operations.

### Features
- **Connection Pooling**: Thread-safe connection management
- **Batch Operations**: Efficient bulk inserts and updates
- **Type Conversion**: Automatic conversion of Python types to PostgreSQL-compatible formats
- **Test Mode**: Safe testing with automatic rollback
- **Smart Error Handling**: Detailed error messages and suggestions

### Quick Start

```python
from WrenchCL.Connect import RdsServiceGateway

# Single connection mode
gateway = RdsServiceGateway()

# Multi-threaded with connection pool
gateway = RdsServiceGateway(
    multithreaded=True,
    min_pool_size=2,
    max_pool_size=20
)
```

### Data Retrieval

```python
# Fetch single record
user = gateway.get_data(
    "SELECT * FROM users WHERE id = %s",
    payload=(user_id,),
    fetchall=False
)

# Fetch multiple records as dictionaries
users = gateway.get_data(
    "SELECT id, name, email FROM users WHERE active = %s",
    payload=(True,),
    return_dict=True
)

# Fetch with debugging
results = gateway.get_data(
    "SELECT * FROM complex_view WHERE date > %s",
    payload=(start_date,),
    show_query=True,  # Logs the actual SQL query
    raise_on_error=True
)
```

### Data Updates

#### Single Record Updates
```python
# Insert single record
gateway.update_database(
    "INSERT INTO users (name, email) VALUES (%s, %s)",
    payload=("John Doe", "john@example.com")
)

# Update with return values
updated_ids = gateway.update_database(
    "UPDATE users SET last_login = NOW() WHERE id = %s RETURNING id",
    payload=(user_id,),
    returning=True
)
```

#### Batch Operations
```python
# Batch insert with list of tuples
user_data = [
    ("Alice", "alice@example.com"),
    ("Bob", "bob@example.com"),
    ("Charlie", "charlie@example.com")
]

gateway.update_database(
    "INSERT INTO users (name, email) VALUES (%s, %s)",
    payload=user_data
)

# DataFrame batch insert
import pandas as pd
df = pd.DataFrame({
    'name': ['David', 'Eve'],
    'email': ['david@example.com', 'eve@example.com'],
    'age': [30, 25]
})

gateway.update_database(
    "INSERT INTO users (name, email, age) VALUES (%s, %s, %s)",
    payload=df,
    column_order=['name', 'email', 'age']
)
```

### Test Mode

```python
# Enable test mode for safe testing
gateway.set_test_mode(True)

# All operations will be rolled back
gateway.update_database(
    "INSERT INTO users (name) VALUES (%s)",
    payload=("Test User",)
)
# Changes are automatically rolled back

# Or per-operation test mode
gateway.update_database(
    "DELETE FROM temp_data",
    test_mode=True  # This specific operation will be rolled back
)
```

### Type Conversions

The gateway automatically converts Python types to PostgreSQL-compatible formats:

```python
import json
from datetime import datetime, timedelta
from uuid import UUID

# Complex data types are automatically handled
complex_data = {
    'json_field': {'nested': 'data'},  # → JSON string
    'datetime_field': datetime.now(),   # → PostgreSQL timestamp
    'timedelta_field': timedelta(hours=2),  # → seconds (float)
    'uuid_field': UUID('12345678-1234-5678-9012-123456789abc'),  # → string
    'list_field': [1, 2, 3]  # → JSON string
}

gateway.update_database(
    "INSERT INTO complex_table (data, created_at, duration, id, tags) VALUES (%s, %s, %s, %s, %s)",
    payload=tuple(complex_data.values())
)
```

---

## S3ServiceGateway

Comprehensive S3 operations with intelligent retry logic and validation.

### Features
- **Multiple Input Types**: Handles file paths, URLs, bytes, Base64, and streams
- **Automatic Retry**: Built-in retry logic for transient failures
- **MIME Type Detection**: Automatic file type detection and validation
- **Signed URLs**: Generate secure, time-limited access URLs
- **Test Mode**: Safe testing without actual S3 modifications

### Quick Start

```python
from WrenchCL.Connect import S3ServiceGateway

gateway = S3ServiceGateway()

# Enable test mode for development
gateway.set_test_mode(True)
```

### File Upload Operations

```python
# Upload from file path
gateway.upload_file(
    file="/path/to/document.pdf",
    bucket_name="my-bucket",
    object_key="documents/document.pdf",
    return_url=True
)

# Upload from bytes
image_bytes = b"binary image data..."
gateway.upload_file(
    file=image_bytes,
    bucket_name="images-bucket", 
    object_key="uploads/image.jpg"
)

# Upload from Base64 string
base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
s3_url = gateway.upload_file(
    file=base64_data,
    bucket_name="my-bucket",
    object_key="images/pixel.png",
    return_url=True
)

# Upload from URL (downloads then uploads)
gateway.upload_file(
    file="https://example.com/remote-file.pdf",
    bucket_name="my-bucket",
    object_key="imported/remote-file.pdf"
)
```

### File Download Operations

```python
# Download to memory
file_stream = gateway.get_object("my-bucket", "documents/file.pdf")
content = file_stream.read()

# Download to local file
gateway.download_object(
    bucket_name="my-bucket",
    object_key="documents/file.pdf", 
    local_path="/downloads/file.pdf"
)

# Get file metadata
headers = gateway.get_object_headers("my-bucket", "documents/file.pdf")
file_size = headers['ContentLength']
last_modified = headers['LastModified']
```

### File Management

```python
# Check if file exists
exists = gateway.check_object_existence("my-bucket", "path/to/file.jpg")

# Copy file between buckets
gateway.copy_object(
    src_bucket_name="source-bucket",
    src_object_key="path/source-file.pdf",
    dst_bucket_name="dest-bucket", 
    dst_object_key="path/dest-file.pdf"
)

# Move file (copy + delete original)
gateway.move_object(
    src_bucket_name="temp-bucket",
    src_object_key="temp/file.pdf",
    dst_bucket_name="permanent-bucket",
    dst_object_key="permanent/file.pdf"
)

# Delete file
gateway.delete_object("my-bucket", "temp/old-file.pdf")
```

### Bucket Operations

```python
# List all buckets
buckets = gateway.list_buckets()

# List objects in bucket
files = gateway.list_objects("my-bucket", prefix="uploads/2024/")

# Check bucket permissions
acl = gateway.check_bucket_permissions("my-bucket")
```

### Signed URLs

```python
# Generate temporary download URL (1 hour expiry)
download_url = gateway.get_signed_url(
    bucket_name="private-bucket",
    object_key="confidential/report.pdf",
    expiration_seconds=3600
)

# Generate long-term access URL (24 hours)
long_term_url = gateway.get_signed_url(
    bucket_name="shared-bucket", 
    object_key="public/presentation.pdf",
    expiration_seconds=86400  # 24 hours
)
```

### MIME Type Handling

```python
# Automatic extension correction
corrected_key = gateway.verify_and_correct_extension(
    object_key="document.txt",  # Wrong extension
    mime_type="application/pdf"  # Actual type
)
# Returns: "document.pdf"

# Upload with automatic correction
gateway.upload_file(
    file=pdf_bytes,
    bucket_name="documents",
    object_key="report.txt"  # Will be corrected to "report.pdf"
)
```

---

## handle_lambda_response

Standardized Lambda response handling with detailed error logging and HTTP status code mapping.

### Features
- **Custom Error Codes**: Internal tracking codes for detailed monitoring
- **HTTP Status Mapping**: Automatic mapping to proper HTTP response codes
- **Structured Logging**: Detailed error context for debugging
- **CORS Headers**: Automatic CORS support for web applications
- **Early Exit Pattern**: Clean Lambda function termination

### Quick Start

```python
from WrenchCL.Connect import handle_lambda_response, GuardedResponseTrigger

def lambda_handler(event, context):
    try:
        # Your Lambda logic here
        result = process_request(event)
        
        # Success response
        handle_lambda_response(
            code=200,
            message="Request processed successfully",
            params={"event": str(event), "context": str(context)},
            response_body={"data": result}
        )
        
    except GuardedResponseTrigger as response:
        return response.get_response()
    except Exception as e:
        # Error response
        handle_lambda_response(
            code=500,
            message=f"Processing failed: {str(e)}",
            params={"event": str(event), "context": str(context)},
            client_id=event.get("client_id"),
            entity_id=event.get("user_id")
        )
```

### Error Code System

#### Client Error Codes (4xx)
```python
# Validation errors
handle_lambda_response(
    code=400,
    message="Invalid request format",
    params=params,
    response_body={"errors": ["Missing required field: email"]}
)

# Authentication errors  
handle_lambda_response(
    code=401,
    message="Session expired",
    params=params,
    client_id=user_id
)

# Permission errors
handle_lambda_response(
    code=403, 
    message="Insufficient permissions for this operation",
    params=params,
    entity_id=resource_id
)

# Not found errors
handle_lambda_response(
    code=404,
    message="User not found",
    params=params,
    entity_id=user_id
)
```

#### Server Error Codes (5xx)
```python
# General server errors
handle_lambda_response(
    code=500,
    message="Database connection failed", 
    params=params
)

# External service failures
handle_lambda_response(
    code=502,
    message="Payment service unavailable",
    params=params
)

# Service unavailable
handle_lambda_response(
    code=503,
    message="System maintenance in progress",
    params=params
)

# Timeout errors
handle_lambda_response(
    code=504,
    message="Request timeout exceeded",
    params=params
)
```

#### Custom Error Codes (5xx Internal)
```python
# Custom tracking codes (mapped to HTTP 500)
handle_lambda_response(
    code=550,  # Generic custom error
    message="Unspecified processing error",
    params=params
)

handle_lambda_response(
    code=551,  # Data validation error
    message="Business rule validation failed",
    params=params
)

handle_lambda_response(
    code=552,  # Resource conflict
    message="Resource is locked by another process",
    params=params
)

handle_lambda_response(
    code=553,  # Model/AI error
    message="ML model inference failed", 
    params=params
)

handle_lambda_response(
    code=554,  # Lambda/API Gateway error
    message="Integration configuration error",
    params=params
)
```

### Advanced Usage

#### Custom Response Bodies
```python
# Success with detailed response
handle_lambda_response(
    code=200,
    message="User created successfully",
    params=params,
    response_body={
        "user": {
            "id": user_id,
            "email": user_email,
            "created_at": timestamp
        },
        "next_steps": [
            "Verify email address",
            "Complete profile setup"
        ]
    }
)

# Error with debugging information
handle_lambda_response(
    code=400,
    message="Validation failed",
    params=params,
    response_body={
        "errors": [
            {"field": "email", "message": "Invalid email format"},
            {"field": "age", "message": "Must be between 18 and 120"}
        ],
        "request_id": request_id
    }
)
```

#### Context Tracking
```python
# Track user and organization context
handle_lambda_response(
    code=403,
    message="Quota exceeded for organization",
    params={
        "event": str(event),
        "context": str(context),
        "start_time": start_time,
        "lambda_client": boto3.client('lambda')
    },
    client_id=event.get("user_id"),
    entity_id=event.get("organization_id")
)
```

### Response Format

All responses follow a consistent structure:

```json
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": "*"
    },
    "body": "{\"Message\": \"Success\", \"data\": {...}}"
}
```

Error responses include detailed logging for monitoring and debugging while returning appropriate HTTP status codes to clients.

---

## Best Practices

### Connection Management
```python
# Use connection pooling for high-concurrency applications
rds = RdsServiceGateway(multithreaded=True, max_pool_size=20)

# Always use test mode during development
rds.set_test_mode(True)
s3.set_test_mode(True)
```

### Error Handling
```python
# Graceful error handling with detailed logging
try:
    result = rds.get_data(query, payload, raise_on_error=True)
except Exception as e:
    handle_lambda_response(
        code=500,
        message=f"Database query failed: {str(e)}",
        params={"query": query, "payload": str(payload)},
        client_id=user_id
    )
```

### Configuration Management
```python
# Use environment-specific configuration
hub = AwsClientHub(env_path=f".env.{environment}")

# Validate configuration on startup
try:
    # Test connections
    s3_client = hub.s3
    db_connection = hub.db
    logger.info("All AWS connections successful")
except Exception as e:
    logger.error(f"AWS connection failed: {e}")
    sys.exit(1)
```

### Security
```python
# Use IAM roles instead of access keys when possible
# Implement least-privilege access
# Use VPC endpoints for S3 access
# Always use SSL/TLS for database connections

# Example: Secure S3 operations
signed_url = s3.get_signed_url(
    bucket_name="secure-bucket",
    object_key="confidential/file.pdf", 
    expiration_seconds=300  # 5 minutes only
)
```